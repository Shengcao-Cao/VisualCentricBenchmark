import { onMounted } from "vue";
import { useRenderImage } from "./useRenderImage";
import { useSessionStore } from "../stores/session.store";
import { useThreadStore } from "../stores/thread.store";

export function useSessionBoot(): void {
  const sessionStore = useSessionStore();
  const threadStore = useThreadStore();
  const { getRenderUrl } = useRenderImage();

  onMounted(() => {
    void (async () => {
      sessionStore.hydrate();
      threadStore.hydrate();
      threadStore.pruneSessions(sessionStore.sessions.map((item) => item.id));

      await sessionStore.ensureSelectedExists();
      threadStore.pruneSessions(sessionStore.sessions.map((item) => item.id));

      for (const session of sessionStore.sessions) {
        const turns = threadStore.getTurns(session.id);
        for (const turn of turns) {
          if (!turn.renderId || turn.renderUrl) continue;
          try {
            const renderUrl = await getRenderUrl(session.id, turn.renderId);
            threadStore.setRenderUrl(session.id, turn.id, renderUrl);
          } catch {
            // Render may have expired server-side; keep the turn without preview.
          }
        }
      }
    })();
  });
}

