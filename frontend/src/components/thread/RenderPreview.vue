<template>
  <div class="preview">
    <img v-if="renderUrl" :src="renderUrl" alt="Generated diagram" />
    <div v-else class="placeholder mono">
      <AppIcon name="triangle-right" :size="28" />
      <span>diagram preview</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import AppIcon from "../ui/AppIcon.vue";

defineProps<{ renderUrl: string | null }>();
</script>

<style scoped>
.preview {
  height: 220px;
  display: grid;
  place-items: center;
  background: #f8f8f8;
}

.preview img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.placeholder {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  color: #bbb;
  font-size: 12px;
}
</style>
