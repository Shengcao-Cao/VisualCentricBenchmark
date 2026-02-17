<template>
  <select class="pill mono" :value="modelValue" @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)">
    <option value="auto">auto</option>
    <option value="tikz">tikz</option>
    <option value="matplotlib">matplotlib</option>
    <option value="graphviz">graphviz</option>
  </select>
</template>

<script setup lang="ts">
defineProps<{ modelValue: string }>();
defineEmits<{ (event: "update:modelValue", value: string): void }>();
</script>

<style scoped>
.pill {
  height: 24px;
  border: 1px solid #e5e5e5;
  border-radius: 4px;
  background: #fafafa;
  color: #666;
  font-size: 10px;
}
</style>

