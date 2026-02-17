import { defineStore } from "pinia";
import { computed, ref } from "vue";
import type { BackendName, ProcessStep, ThreadTurn } from "../types/domain";
import { makeId } from "../utils/ids";
import { backendFromTool, toolLabel } from "../services/adapters/sse-event.adapter";

const STORAGE_KEY = "vcb.frontend.thread";

interface PersistedThreadState {
  turnsBySession: Record<string, ThreadTurn[]>;
  draftBySession: Record<string, string>;
}

export const useThreadStore = defineStore("thread", () => {
  const turnsBySession = ref<Record<string, ThreadTurn[]>>({});
  const draftBySession = ref<Record<string, string>>({});

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
    const payload: PersistedThreadState = {
      turnsBySession: turnsBySession.value,
      draftBySession: draftBySession.value
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  }

  function hydrate(): void {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw) as PersistedThreadState;
      turnsBySession.value = parsed.turnsBySession ?? {};
      draftBySession.value = parsed.draftBySession ?? {};

      for (const turns of Object.values(turnsBySession.value)) {
        for (const turn of turns) {
          // A page reload cannot continue a live stream; mark any stale stream as closed.
          if (turn.isStreaming) turn.isStreaming = false;
        }
      }
    } catch {
      localStorage.removeItem(STORAGE_KEY);
    }
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

  function startTool(sessionId: string, turnId: string, tool: string, input: string): void {
    const turn = findTurn(sessionId, turnId);
    if (!turn) return;

    const step: ProcessStep = {
      id: makeId("step"),
      tool,
      label: toolLabel(tool),
      input,
      status: "running"
    };

    turn.steps.push(step);

    const maybeBackend = backendFromTool(tool);
    if (maybeBackend !== "unknown") {
      turn.backend = maybeBackend;
    }

    persist();
  }

  function finishTool(sessionId: string, turnId: string, tool: string): void {
    const turn = findTurn(sessionId, turnId);
    if (!turn) return;

    const step = [...turn.steps].reverse().find((candidate) => candidate.tool === tool && candidate.status === "running");
    if (!step) return;
    step.status = "done";
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

