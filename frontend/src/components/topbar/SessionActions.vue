<template>
  <div class="actions">
    <button class="action-btn" type="button" @click="$emit('new')">
      <AppIcon name="plus" :size="13" />
      <span>New session</span>
    </button>
    <button class="icon-btn" type="button" @click="$emit('settings')" aria-label="Settings">
      <AppIcon name="settings" :size="14" />
    </button>
  </div>
</template>

<script setup lang="ts">
import AppIcon from "../ui/AppIcon.vue";

defineEmits<{
  (event: "new"): void;
  (event: "settings"): void;
}>();
</script>

<style scoped>
.actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.action-btn,
.icon-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 30px;
  border-radius: 6px;
  border: 1px solid #e5e5e5;
  background: #fff;
  color: #666;
  padding: 0 12px;
  cursor: pointer;
}

.icon-btn {
  padding: 0 10px;
}
</style>

