<template>
  <div class="thread scroll-y">
    <div class="inner">
      <template v-for="turn in turns" :key="turn.id">
        <PromptMessageCard :prompt="turn.prompt" />
        <ResponseCard :turn="turn" />
        <div class="divider" />
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ThreadTurn } from "../../types/domain";
import PromptMessageCard from "./PromptMessageCard.vue";
import ResponseCard from "./ResponseCard.vue";

defineProps<{ turns: ThreadTurn[] }>();
</script>

<style scoped>
.thread {
  height: 100%;
  padding: 24px 40px 0;
  min-height: 0;
}

.inner {
  max-width: 780px;
  margin: 0 auto;
}

.divider {
  height: 1px;
  background: #e5e5e5;
  margin: 0;
}
</style>

