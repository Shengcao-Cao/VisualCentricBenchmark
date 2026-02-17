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
  min-height: 220px;
  max-height: 220px;
  width: 100%;
  position: relative;
  background: #f8f8f8;
  overflow: hidden;
}

.preview img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.placeholder {
  height: 100%;
  width: 100%;
  justify-content: center;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  color: #bbb;
  font-size: 12px;
}
</style>
