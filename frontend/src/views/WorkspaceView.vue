<template>
  <div class="app-shell">
    <TopBar :session-label="sessionLabel" @new="onNewSession" @settings="toggleSettings" />

    <div class="body-shell">
      <div class="sidebar">
        <SessionSidebar
          :sessions="sessionStore.sessions"
          :selected-session-id="sessionStore.selectedSessionId"
          @select="sessionStore.select"
          @new="onNewSession"
        />
      </div>

      <main class="main">
        <EmptyStatePanel
          v-if="turns.length === 0"
          :draft="draft"
          :disabled="isStreaming"
          @pick="onPickExample"
          @update:draft="onDraftChange"
          @submit="onSubmit"
        />
        <ThreadView v-else :turns="turns" />

        <div v-if="turns.length > 0" class="composer-shell">
          <div class="composer-inner">
            <PromptComposer
              :model-value="draft"
              :disabled="isStreaming"
              @update:model-value="onDraftChange"
              @submit="onSubmit"
            />
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import TopBar from "../components/topbar/TopBar.vue";
import SessionSidebar from "../components/sidebar/SessionSidebar.vue";
import PromptComposer from "../components/composer/PromptComposer.vue";
import EmptyStatePanel from "../components/empty/EmptyStatePanel.vue";
import ThreadView from "../components/thread/ThreadView.vue";
import { useSessionBoot } from "../composables/useSessionBoot";
import { useSessionStore } from "../stores/session.store";
import { useThreadStore } from "../stores/thread.store";
import { useUiStore } from "../stores/ui.store";
import { useConversation } from "../composables/useConversation";

useSessionBoot();

const sessionStore = useSessionStore();
const threadStore = useThreadStore();
const uiStore = useUiStore();
const { startNewSession, sendPrompt } = useConversation();
const unsavedDraft = ref("");

const turns = computed(() => threadStore.getTurns(sessionStore.selectedSessionId));
const draft = computed(() => {
  if (!sessionStore.selectedSessionId) return unsavedDraft.value;
  return threadStore.getDraft(sessionStore.selectedSessionId);
});

const sessionLabel = computed(() => {
  if (!sessionStore.selectedSessionId) return "New session";
  return `Session #${sessionStore.selectedSessionId.slice(0, 6)}`;
});

const isStreaming = computed(() => {
  const sessionId = sessionStore.selectedSessionId;
  if (!sessionId) return false;
  return threadStore.isStreamingBySession[sessionId] ?? false;
});

function toggleSettings(): void {
  uiStore.toggleSettings();
}

async function onNewSession(): Promise<void> {
  await startNewSession();
}

function onDraftChange(value: string): void {
  if (!sessionStore.selectedSessionId) {
    unsavedDraft.value = value;
    return;
  }
  threadStore.setDraft(sessionStore.selectedSessionId, value);
}

function onPickExample(value: string): void {
  if (!sessionStore.selectedSessionId) {
    unsavedDraft.value = value;
    return;
  }
  threadStore.setDraft(sessionStore.selectedSessionId, value);
}

function onSubmit(payload: { prompt: string; backend: string; maxTurns: number }): void {
  void payload.backend;
  void payload.maxTurns;
  unsavedDraft.value = "";
  void sendPrompt(payload.prompt);
}
</script>

<style scoped>
.composer-shell {
  border-top: 1px solid #e5e5e5;
  background: #fff;
  padding: 14px 0;
}

.composer-inner {
  max-width: 780px;
  margin: 0 auto;
  padding: 0 24px;
}
</style>

