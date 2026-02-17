import { useSessionStore } from "../stores/session.store";
import { useThreadStore } from "../stores/thread.store";
import { streamSessionMessage } from "../services/api/stream.api";
import { useRenderImage } from "./useRenderImage";
import type {
  ErrorPayload,
  RenderReadyPayload,
  TextDeltaPayload,
  ToolResultPayload,
  ToolStartPayload,
  TurnCompletePayload,
  ValidateResultPayload
} from "../types/api";
import { toRelativeLabel } from "../utils/time";

export function useConversation() {
  const sessionStore = useSessionStore();
  const threadStore = useThreadStore();
  const { getRenderUrl } = useRenderImage();

  async function ensureSession(): Promise<string> {
    if (sessionStore.selectedSessionId) {
      return sessionStore.selectedSessionId;
    }
    return sessionStore.createAndSelect();
  }

  async function startNewSession(): Promise<string> {
    return sessionStore.createAndSelect();
  }

  async function sendPrompt(prompt: string): Promise<void> {
    const trimmed = prompt.trim();
    if (!trimmed) return;

    const sessionId = await ensureSession();
    threadStore.setDraft(sessionId, "");
    const turnId = threadStore.addTurn(sessionId, trimmed);

    sessionStore.updateMeta(sessionId, {
      title: trimmed.length > 60 ? `${trimmed.slice(0, 60)}...` : trimmed,
      lastActiveLabel: "today"
    });

    await streamSessionMessage(sessionId, trimmed, async ({ event, data }) => {
      if (event === "text_delta") {
        threadStore.appendReplyDelta(sessionId, turnId, (data as TextDeltaPayload).delta);
        return;
      }

      if (event === "tool_start") {
        const payload = data as ToolStartPayload;
        threadStore.startTool(sessionId, turnId, payload.tool, payload.input);
        return;
      }

      if (event === "tool_result") {
        const payload = data as ToolResultPayload;
        threadStore.finishTool(sessionId, turnId, payload.tool);
        return;
      }

      if (event === "render_ready") {
        const payload = data as RenderReadyPayload;
        threadStore.setRender(sessionId, turnId, payload.render_id);
        const renderUrl = await getRenderUrl(sessionId, payload.render_id);
        threadStore.setRenderUrl(sessionId, turnId, renderUrl);
        return;
      }

      if (event === "validate_result") {
        const payload = data as ValidateResultPayload;
        threadStore.setValidation(
          sessionId,
          turnId,
          payload.score,
          payload.passed,
          payload.issues,
          payload.suggestions
        );
        return;
      }

      if (event === "turn_complete") {
        const payload = data as TurnCompletePayload;
        threadStore.setTurnReply(sessionId, turnId, payload.reply ?? "");
        threadStore.finishTurn(sessionId, turnId);

        const turns = threadStore.getTurns(sessionId);
        sessionStore.updateMeta(sessionId, {
          exchanges: turns.length,
          lastActiveLabel: toRelativeLabel(Date.now())
        });
        return;
      }

      if (event === "error") {
        threadStore.failTurn(sessionId, turnId, (data as ErrorPayload).message);
      }
    }).catch((error: unknown) => {
      const message = error instanceof Error ? error.message : String(error);
      threadStore.failTurn(sessionId, turnId, message);
    });
  }

  return {
    ensureSession,
    startNewSession,
    sendPrompt
  };
}

