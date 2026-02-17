<template>
  <form class="composer card" @submit.prevent="onSubmit">
    <textarea
      class="input"
      :value="modelValue"
      @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
      placeholder="Describe a diagram..."
      rows="3"
    />
    <div class="footer">
      <div class="left">
        <BackendSelect v-model="backend" />
        <MaxTurnsSelect v-model="maxTurns" />
        <span class="mono chars">{{ modelValue.length }} chars</span>
      </div>
      <SubmitButton :disabled="disabled || !modelValue.trim()" />
    </div>
  </form>
</template>

<script setup lang="ts">
import { ref } from "vue";
import BackendSelect from "./BackendSelect.vue";
import MaxTurnsSelect from "./MaxTurnsSelect.vue";
import SubmitButton from "./SubmitButton.vue";

const props = defineProps<{
  modelValue: string;
  disabled?: boolean;
}>();

const emit = defineEmits<{
  (event: "update:modelValue", value: string): void;
  (event: "submit", payload: { prompt: string; backend: string; maxTurns: number }): void;
}>();

const backend = ref("auto");
const maxTurns = ref(10);

function onSubmit(): void {
  emit("submit", {
    prompt: props.modelValue,
    backend: backend.value,
    maxTurns: maxTurns.value
  });
}
</script>

<style scoped>
.composer {
  padding: 12px 14px;
  display: grid;
  gap: 8px;
}

.input {
  border: 0;
  resize: vertical;
  min-height: 66px;
  outline: none;
  font-family: "Newsreader", serif;
  font-size: 16px;
}

.footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chars {
  color: #bbb;
  font-size: 10px;
}
</style>

