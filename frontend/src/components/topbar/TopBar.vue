<template>
  <header class="topbar">
    <div class="brand">
      <AppIcon name="aperture" :size="18" color="#0D6E6E" />
      <span>VisualCentricBenchmark</span>
    </div>
    <div class="right mono">
      <span>{{ sessionLabel }}</span>
      <span class="dot" />
      <SessionActions @new="$emit('new')" @settings="$emit('settings')" />
    </div>
  </header>
</template>

<script setup lang="ts">
import SessionActions from "./SessionActions.vue";
import AppIcon from "../ui/AppIcon.vue";

defineProps<{
  sessionLabel: string;
}>();

defineEmits<{
  (event: "new"): void;
  (event: "settings"): void;
}>();
</script>

<style scoped>
.topbar {
  height: 52px;
  border-bottom: 1px solid #e5e5e5;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-family: "Newsreader", serif;
  font-size: 18px;
  font-weight: 500;
}

.right {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #888;
  font-size: 11px;
}

.dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #ccc;
}
</style>

