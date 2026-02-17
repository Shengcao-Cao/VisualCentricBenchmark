<template>
  <aside class="sidebar-inner">
    <div class="header mono">
      <span>SESSIONS</span>
      <button type="button" class="new-mini" @click="$emit('new')" aria-label="New session">
        <AppIcon name="plus" :size="14" />
      </button>
    </div>
    <EmptySessionsHint v-if="sessions.length === 0" />
    <div v-else>
      <SessionListItem
        v-for="item in sessions"
        :key="item.id"
        :session="item"
        :active="item.id === selectedSessionId"
        @select="$emit('select', item.id)"
      />
    </div>
  </aside>
</template>

<script setup lang="ts">
import type { SessionEntry } from "../../types/domain";
import SessionListItem from "./SessionListItem.vue";
import EmptySessionsHint from "./EmptySessionsHint.vue";
import AppIcon from "../ui/AppIcon.vue";

defineProps<{
  sessions: SessionEntry[];
  selectedSessionId: string | null;
}>();

defineEmits<{
  (event: "select", sessionId: string): void;
  (event: "new"): void;
}>();
</script>

<style scoped>
.sidebar-inner {
  padding-top: 18px;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 14px;
  color: #aaa;
  font-size: 10px;
  letter-spacing: 1.4px;
}

.new-mini {
  border: 0;
  background: transparent;
  color: #999;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>

