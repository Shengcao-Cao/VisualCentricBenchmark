<template>
  <section class="prompt">
    <div class="meta mono">
      <AppIcon name="user" :size="12" />
      <span>PROMPT</span>
    </div>
    <div class="text">{{ prompt }}</div>
  </section>
</template>

<script setup lang="ts">
import AppIcon from "../ui/AppIcon.vue";

defineProps<{ prompt: string }>();
</script>

<style scoped>
.prompt {
  padding: 16px 0 14px;
}

.meta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 10px;
  color: #aaa;
  letter-spacing: 1.4px;
}

.text {
  margin-top: 6px;
  font-family: "Newsreader", serif;
  font-size: 18px;
  color: #1a1a1a;
}
</style>

