<template>
  <div class="hint mono">
    <AppIcon name="history" :size="18" />
    <span>No sessions yet</span>
  </div>
</template>

<script setup lang="ts">
import AppIcon from "../ui/AppIcon.vue";
</script>

<style scoped>
.hint {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #b5b5b5;
  font-size: 12px;
  padding: 20px 14px;
}
</style>

