import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { createSession, getSession } from "../services/api/sessions.api";
import { toSessionEntry } from "../services/adapters/session.adapter";
import type { SessionEntry } from "../types/domain";

const STORAGE_KEY = "vcb.frontend.sessions";

interface PersistedSessions {
  selectedSessionId: string | null;
  sessions: SessionEntry[];
}

export const useSessionStore = defineStore("session", () => {
  const sessions = ref<SessionEntry[]>([]);
  const selectedSessionId = ref<string | null>(null);
  const isBusy = ref(false);

  const selectedSession = computed(() =>
    sessions.value.find((item) => item.id === selectedSessionId.value) ?? null
  );

  function persist(): void {
    const payload: PersistedSessions = {
      selectedSessionId: selectedSessionId.value,
      sessions: sessions.value
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  }

  function hydrate(): void {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw) as PersistedSessions;
      sessions.value = parsed.sessions ?? [];
      selectedSessionId.value = parsed.selectedSessionId ?? parsed.sessions?.[0]?.id ?? null;
    } catch {
      localStorage.removeItem(STORAGE_KEY);
    }
  }

  function select(sessionId: string): void {
    selectedSessionId.value = sessionId;
    persist();
  }

  async function ensureSelectedExists(): Promise<string | null> {
    while (selectedSessionId.value) {
      const id = selectedSessionId.value;
      try {
        await getSession(id);
        return id;
      } catch {
        sessions.value = sessions.value.filter((item) => item.id !== id);
        selectedSessionId.value = sessions.value[0]?.id ?? null;
        persist();
      }
    }
    return null;
  }

  async function createAndSelect(): Promise<string> {
    isBusy.value = true;
    try {
      const created = await createSession();
      const info = await getSession(created.session_id);
      const entry = toSessionEntry(info);
      sessions.value = [entry, ...sessions.value.filter((s) => s.id !== entry.id)];
      selectedSessionId.value = entry.id;
      persist();
      return entry.id;
    } finally {
      isBusy.value = false;
    }
  }

  function updateMeta(sessionId: string, patch: Partial<SessionEntry>): void {
    const index = sessions.value.findIndex((item) => item.id === sessionId);
    if (index === -1) return;
    sessions.value[index] = { ...sessions.value[index], ...patch };
    persist();
  }

  return {
    sessions,
    selectedSessionId,
    selectedSession,
    isBusy,
    hydrate,
    select,
    ensureSelectedExists,
    createAndSelect,
    updateMeta,
    persist
  };
});

