<template>
  <div class="steps">
    <div class="label mono">PROCESS</div>
    <div v-for="step in steps" :key="step.id" class="row">
      <span>{{ step.label }}</span>
      <span class="status-wrap">
        <AppIcon v-if="step.status === 'done'" name="check" :size="10" color="#0D6E6E" />
        <AppIcon v-else name="loader" :size="10" color="#0D6E6E" :spin="true" />
        <span class="mono status">{{ step.status }}</span>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ProcessStep } from "../../types/domain";
import AppIcon from "../ui/AppIcon.vue";

defineProps<{ steps: ProcessStep[] }>();
</script>

<style scoped>
.steps {
  border-bottom: 1px solid #f0f0f0;
  padding: 8px 14px;
}

.label {
  font-size: 9px;
  color: #9a9a9a;
  letter-spacing: 1px;
  margin-bottom: 6px;
}

.row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 11px;
  color: #666;
  padding: 2px 0;
}

.status-wrap {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.status {
  font-size: 10px;
  color: #999;
}
</style>
