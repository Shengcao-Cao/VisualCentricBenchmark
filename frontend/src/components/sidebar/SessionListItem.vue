<template>
  <button :class="['item', active ? 'active' : '']" type="button" @click="$emit('select')">
    <div class="title">{{ session.title }}</div>
    <div class="meta mono">{{ session.backend }} · {{ session.exchanges }} exchanges · {{ session.lastActiveLabel }}</div>
  </button>
</template>

<script setup lang="ts">
import type { SessionEntry } from "../../types/domain";

defineProps<{
  session: SessionEntry;
  active: boolean;
}>();

defineEmits<{
  (event: "select"): void;
}>();
</script>

<style scoped>
.item {
  width: 100%;
  text-align: left;
  background: transparent;
  border: 0;
  padding: 10px 14px;
  cursor: pointer;
}

.item:hover {
  background: #f8f8f8;
}

.item.active {
  background: #f0faf9;
  border-left: 2px solid #0d6e6e;
}

.title {
  font-family: "Newsreader", serif;
  font-size: 13px;
  color: #1a1a1a;
}

.meta {
  margin-top: 3px;
  font-size: 10px;
  color: #999;
}
</style>

