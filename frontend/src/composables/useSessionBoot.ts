import { onMounted } from "vue";
import { useSessionStore } from "../stores/session.store";

export function useSessionBoot(): void {
  const sessionStore = useSessionStore();

  onMounted(() => {
    sessionStore.hydrate();
  });
}

