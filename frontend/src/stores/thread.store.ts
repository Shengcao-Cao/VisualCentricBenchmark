import { defineStore } from "pinia";
import { computed, ref } from "vue";
import type { BackendName, ProcessStep, ThreadTurn } from "../types/domain";
import type { ToolResultPayload, ToolStartPayload } from "../types/api";
import { makeId } from "../utils/ids";
import { createIdbStringStore } from "../utils/idb";
import { backendFromTool, toolLabel } from "../services/adapters/sse-event.adapter";

const STORAGE_KEY = "vcb.frontend.thread";
const PERSIST_THROTTLE_MS = 300;
const INLINE_STRING_MAX_CHARS = 1024;
const BLOB_KEY_VERSION = "v1";
const TURN_BLOB_STEP_ID = "turn";

const blobStore = createIdbStringStore({
  dbName: "vcb.frontend",
  storeName: "thread-blobs"
});

interface PersistedProcessStep extends Omit<ProcessStep, "inputFull" | "resultText"> {
  inputFull?: string | null;
  inputFullBlobKey?: string | null;
  resultText?: string | null;
  resultTextBlobKey?: string | null;
}

interface PersistedThreadTurn extends Omit<ThreadTurn, "reply" | "steps"> {
  reply: string;
  replyBlobKey?: string | null;
  steps: PersistedProcessStep[];
}

interface PersistedThreadState {
  turnsBySession: Record<string, PersistedThreadTurn[]>;
  draftBySession: Record<string, string>;
}

export const useThreadStore = defineStore("thread", () => {
  const turnsBySession = ref<Record<string, ThreadTurn[]>>({});
  const draftBySession = ref<Record<string, string>>({});
  let persistTimer: ReturnType<typeof setTimeout> | null = null;
  let persistInFlight = false;
  let persistQueued = false;

  const isStreamingBySession = computed<Record<string, boolean>>(() => {
    const result: Record<string, boolean> = {};
    for (const [sessionId, turns] of Object.entries(turnsBySession.value)) {
      result[sessionId] = turns.some((turn) => turn.isStreaming);
    }
    return result;
  });

  function getTurns(sessionId: string | null): ThreadTurn[] {
    if (!sessionId) return [];
    return turnsBySession.value[sessionId] ?? [];
  }

  function getDraft(sessionId: string | null): string {
    if (!sessionId) return "";
    return draftBySession.value[sessionId] ?? "";
  }

  function persist(): void {
    schedulePersist();
  }

  async function persistNow(): Promise<void> {
    if (persistInFlight) {
      persistQueued = true;
      return;
    }
    persistInFlight = true;

    try {
      const serializedTurnsBySession = await Promise.all(
        Object.entries(turnsBySession.value).map(async ([sessionId, turns]) => {
          const serializedTurns = await Promise.all(
            turns.map(async (turn) => serializeTurn(sessionId, turn))
          );
          return [sessionId, serializedTurns] as const;
        })
      );

      const payload: PersistedThreadState = {
        turnsBySession: Object.fromEntries(serializedTurnsBySession),
        draftBySession: draftBySession.value
      };

      localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    } catch {
    } finally {
      persistInFlight = false;
      if (persistQueued) {
        persistQueued = false;
        schedulePersist();
      }
    }
  }

  function schedulePersist(): void {
    if (persistTimer) return;
    persistTimer = setTimeout(() => {
      persistTimer = null;
      void persistNow();
    }, PERSIST_THROTTLE_MS);
  }

  async function hydrate(): Promise<void> {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;

    try {
      const parsed = JSON.parse(raw) as PersistedThreadState;
      const hydratedTurnsBySession: Record<string, ThreadTurn[]> = {};
      const blobLoads: Array<{ key: string; apply: (value: string) => void }> = [];

      for (const [sessionId, turns] of Object.entries(parsed.turnsBySession ?? {})) {
        hydratedTurnsBySession[sessionId] = turns.map((persistedTurn) => {
          const turn: ThreadTurn = {
            ...persistedTurn,
            reply: persistedTurn.reply ?? "",
            steps: persistedTurn.steps.map((persistedStep) => {
              const step: ProcessStep = {
                ...persistedStep,
                inputFull: persistedStep.inputFull,
                resultText: persistedStep.resultText,
                stepStatus: persistedStep.stepStatus
              };

              if (persistedStep.inputFullBlobKey && step.inputFull == null) {
                blobLoads.push({
                  key: persistedStep.inputFullBlobKey,
                  apply: (value) => {
                    step.inputFull = value;
                  }
                });
              }

              if (persistedStep.resultTextBlobKey && step.resultText == null) {
                blobLoads.push({
                  key: persistedStep.resultTextBlobKey,
                  apply: (value) => {
                    step.resultText = value;
                  }
                });
              }

              const legacyStatus = (step as { status?: unknown }).status;
              if (!step.stepStatus && (legacyStatus === "running" || legacyStatus === "done")) {
                step.stepStatus = legacyStatus;
                step.status = null;
              }

              return step;
            }),
            renderUrl: null,
            isStreaming: false
          };

          if (persistedTurn.replyBlobKey && !turn.reply) {
            blobLoads.push({
              key: persistedTurn.replyBlobKey,
              apply: (value) => {
                turn.reply = value;
              }
            });
          }

          return turn;
        });
      }

      turnsBySession.value = hydratedTurnsBySession;
      draftBySession.value = parsed.draftBySession ?? {};

      if (blobLoads.length > 0) {
        const blobValues = await blobStore.getMany([...new Set(blobLoads.map((item) => item.key))]);
        for (const load of blobLoads) {
          const value = blobValues[load.key];
          if (typeof value === "string") {
            load.apply(value);
          }
        }
      }
    } catch {
      localStorage.removeItem(STORAGE_KEY);
    }
  }

  async function serializeTurn(sessionId: string, turn: ThreadTurn): Promise<PersistedThreadTurn> {
    const replyBlob = await maybeStoreBlob(
      makeBlobKey(sessionId, turn.id, TURN_BLOB_STEP_ID, "reply"),
      turn.reply
    );

    const steps = await Promise.all(
      turn.steps.map(async (step) => {
        const inputBlob = await maybeStoreBlob(
          makeBlobKey(sessionId, turn.id, step.id, "input_full"),
          step.inputFull
        );
        const resultBlob = await maybeStoreBlob(
          makeBlobKey(sessionId, turn.id, step.id, "result_text"),
          step.resultText
        );

        const persistedStep: PersistedProcessStep = {
          ...step,
          inputFull: inputBlob.value,
          inputFullBlobKey: inputBlob.blobKey,
          resultText: resultBlob.value,
          resultTextBlobKey: resultBlob.blobKey
        };

        return persistedStep;
      })
    );

    return {
      ...turn,
      reply: replyBlob.value ?? "",
      replyBlobKey: replyBlob.blobKey,
      steps,
      renderUrl: null
    };
  }

  async function maybeStoreBlob(
    blobKey: string,
    value: string | null | undefined
  ): Promise<{ value: string | null | undefined; blobKey: string | null }> {
    if (typeof value !== "string") {
      return { value, blobKey: null };
    }
    if (value.length <= INLINE_STRING_MAX_CHARS) {
      return { value, blobKey: null };
    }

    const saved = await blobStore.set(blobKey, value);
    if (!saved) {
      return { value, blobKey: null };
    }

    return { value: null, blobKey };
  }

  function makeBlobKey(sessionId: string, turnId: string, stepId: string, field: string): string {
    return `${BLOB_KEY_VERSION}:${sessionId}:${turnId}:${stepId}:${field}`;
  }

  function pruneSessions(validSessionIds: string[]): void {
    const valid = new Set(validSessionIds);
    turnsBySession.value = Object.fromEntries(
      Object.entries(turnsBySession.value).filter(([sessionId]) => valid.has(sessionId))
    );
    draftBySession.value = Object.fromEntries(
      Object.entries(draftBySession.value).filter(([sessionId]) => valid.has(sessionId))
    );
    persist();
  }

  function setDraft(sessionId: string, value: string): void {
    draftBySession.value[sessionId] = value;
    persist();
  }

  function addTurn(sessionId: string, prompt: string): string {
    const turn: ThreadTurn = {
      id: makeId("turn"),
      prompt,
      reply: "",
      renderId: null,
      renderUrl: null,
      backend: "auto",
      score: null,
      passed: null,
      issues: [],
      suggestions: [],
      steps: [],
      error: null,
      isStreaming: true,
      createdAt: Date.now()
    };

    const existing = turnsBySession.value[sessionId] ?? [];
    turnsBySession.value[sessionId] = [...existing, turn];
    persist();
    return turn.id;
  }

  function appendReplyDelta(sessionId: string, turnId: string, delta: string): void {
    const turn = findTurn(sessionId, turnId);
    if (!turn) return;
    turn.reply += delta;
    persist();
  }

  function setTurnReply(sessionId: string, turnId: string, reply: string): void {
    const turn = findTurn(sessionId, turnId);
    if (!turn) return;
    turn.reply = reply;
    persist();
  }

  function startTool(sessionId: string, turnId: string, payload: ToolStartPayload): void {
    const turn = findTurn(sessionId, turnId);
    if (!turn) return;

    const step: ProcessStep = {
      id: makeId("step"),
      tool: payload.tool,
      label: toolLabel(payload.tool),
      toolUseId: payload.tool_use_id ?? null,
      inputSummary: payload.input,
      inputFull: payload.input_full,
      inputFullSizeBytes: payload.input_full_size_bytes,
      inputTruncated: payload.input_truncated,
      status: null,
      startedAtMs: payload.ts_ms ?? Date.now(),
      endedAtMs: null,
      durationMs: null,
      redaction: payload.redaction,
      size: payload.size,
      stepStatus: "running"
    };

    turn.steps.push(step);

    const maybeBackend = backendFromTool(payload.tool);
    if (maybeBackend !== "unknown") {
      turn.backend = maybeBackend;
    }

    persist();
  }

  function finishTool(sessionId: string, turnId: string, payload: ToolResultPayload): void {
    const turn = findTurn(sessionId, turnId);
    if (!turn) return;

    const step = findRunningStep(turn, payload.tool_use_id, payload.tool);
    if (!step) return;

    const endedAtMs = payload.ts_ms ?? Date.now();
    step.stepStatus = "done";
    step.status = payload.status ?? (payload.error ? "error" : step.status ?? null);
    step.endedAtMs = endedAtMs;
    step.durationMs = payload.duration_ms ?? (typeof step.startedAtMs === "number" ? endedAtMs - step.startedAtMs : null);
    if (payload.result_summary !== undefined) {
      step.resultSummary = payload.result_summary;
    }
    if (payload.result_text !== undefined) {
      step.resultText = payload.result_text;
    }
    if (payload.result_text_size_bytes !== undefined) {
      step.resultTextSizeBytes = payload.result_text_size_bytes;
    }
    if (payload.result_truncated !== undefined) {
      step.resultTruncated = payload.result_truncated;
    }
    if (payload.redaction) {
      step.redaction = payload.redaction;
    }
    if (payload.size) {
      step.size = payload.size;
    }
    if (payload.artifacts !== undefined) {
      step.artifacts = payload.artifacts;
    }
    if (payload.error !== undefined) {
      step.error = payload.error;
    }

    persist();
  }

  function setRender(sessionId: string, turnId: string, renderId: string): void {
    const turn = findTurn(sessionId, turnId);
    if (!turn) return;
    turn.renderId = renderId;
    persist();
  }

  function setRenderUrl(sessionId: string, turnId: string, renderUrl: string): void {
    const turn = findTurn(sessionId, turnId);
    if (!turn) return;
    turn.renderUrl = renderUrl;
    persist();
  }

  function setValidation(
    sessionId: string,
    turnId: string,
    score: number,
    passed: boolean,
    issues: string[],
    suggestions: string[]
  ): void {
    const turn = findTurn(sessionId, turnId);
    if (!turn) return;
    turn.score = score;
    turn.passed = passed;
    turn.issues = issues;
    turn.suggestions = suggestions;
    persist();
  }

  function finishTurn(sessionId: string, turnId: string): void {
    const turn = findTurn(sessionId, turnId);
    if (!turn) return;
    turn.isStreaming = false;
    persist();
  }

  function failTurn(sessionId: string, turnId: string, message: string): void {
    const turn = findTurn(sessionId, turnId);
    if (!turn) return;
    turn.error = message;
    turn.isStreaming = false;
    persist();
  }

  function findTurn(sessionId: string, turnId: string): ThreadTurn | undefined {
    return turnsBySession.value[sessionId]?.find((item) => item.id === turnId);
  }

  function findRunningStep(turn: ThreadTurn, toolUseId?: string, tool?: string): ProcessStep | undefined {
    if (toolUseId) {
      const byToolUseId = [...turn.steps]
        .reverse()
        .find((candidate) => candidate.toolUseId === toolUseId && candidate.stepStatus === "running");
      if (byToolUseId) {
        return byToolUseId;
      }
    }

    if (!tool) return undefined;
    return [...turn.steps]
      .reverse()
      .find((candidate) => candidate.tool === tool && candidate.stepStatus === "running");
  }

  return {
    turnsBySession,
    draftBySession,
    isStreamingBySession,
    persist,
    hydrate,
    pruneSessions,
    getTurns,
    getDraft,
    setDraft,
    addTurn,
    appendReplyDelta,
    setTurnReply,
    startTool,
    finishTool,
    setRender,
    setRenderUrl,
    setValidation,
    finishTurn,
    failTurn
  };
});

