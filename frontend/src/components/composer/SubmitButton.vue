<template>
  <button class="submit" :disabled="disabled" type="submit">
    <AppIcon name="arrow-up" :size="13" color="currentColor" />
    <span>Generate</span>
  </button>
</template>

<script setup lang="ts">
import AppIcon from "../ui/AppIcon.vue";

defineProps<{ disabled: boolean }>();
</script>

<style scoped>
.submit {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 30px;
  border: 0;
  border-radius: 6px;
  background: #0d6e6e;
  color: #fff;
  font-weight: 600;
  padding: 0 14px;
  cursor: pointer;
}

.submit:disabled {
  background: #d7d7d7;
  color: #999;
  cursor: not-allowed;
}
</style>
