<template>
  <select class="pill mono" :value="modelValue" @change="$emit('update:modelValue', Number(($event.target as HTMLSelectElement).value))">
    <option :value="5">max 5 turns</option>
    <option :value="10">max 10 turns</option>
    <option :value="20">max 20 turns</option>
  </select>
</template>

<script setup lang="ts">
defineProps<{ modelValue: number }>();
defineEmits<{ (event: "update:modelValue", value: number): void }>();
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

