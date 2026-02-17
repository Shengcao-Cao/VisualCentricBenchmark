<template>
  <button class="example card" type="button" @click="$emit('pick', text)">
    <AppIcon :name="iconName" :size="16" color="#0D6E6E" />
    <div class="title">{{ text }}</div>
    <div class="tag mono">{{ tag }}</div>
  </button>
</template>

<script setup lang="ts">
import { computed } from "vue";
import AppIcon from "../ui/AppIcon.vue";

type IconName = "triangle-right" | "activity" | "share-2";

const props = defineProps<{
  text: string;
  tag: string;
}>();

const iconName = computed<IconName>(() => {
  if (props.tag === "matplotlib") return "activity";
  if (props.tag === "graphviz") return "share-2";
  return "triangle-right";
});

defineEmits<{
  (event: "pick", value: string): void;
}>();
</script>

<style scoped>
.example {
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-align: left;
  width: 100%;
  padding: 14px;
  border: 1px solid #e5e5e5;
  background: #ffffff;
  border-radius: 8px;
  cursor: pointer;
}

.title {
  font-family: "Newsreader", serif;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.35;
  white-space: pre-line;
  color: #1a1a1a;
}

.tag {
  font-size: 10px;
  color: #aaaaaa;
}
</style>
