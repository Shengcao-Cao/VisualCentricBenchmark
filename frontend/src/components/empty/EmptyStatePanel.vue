<template>
  <section class="empty scroll-y">
    <div class="inner">
      <div class="hero">
        <div class="hero-title">
          <AppIcon name="aperture" :size="36" color="#0D6E6E" />
          <h1>Describe a diagram.</h1>
        </div>
        <p>
          The agent will classify your request, choose the right backend
          (TikZ, Matplotlib, or Graphviz), render, and validate the result.
        </p>
      </div>

      <div class="examples">
        <ExamplePromptCard
          v-for="item in examples"
          :key="item.text"
          :text="item.text"
          :tag="item.tag"
          @pick="$emit('pick', $event)"
        />
      </div>

      <div class="input-area">
        <PromptComposer
          :model-value="draft"
          :disabled="disabled"
          @update:model-value="$emit('update:draft', $event)"
          @submit="$emit('submit', $event)"
        />
        <p class="hint">Try one of the examples above, or write your own.</p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import ExamplePromptCard from "./ExamplePromptCard.vue";
import AppIcon from "../ui/AppIcon.vue";
import PromptComposer from "../composer/PromptComposer.vue";

const examples = [
  { text: "right triangle with legs a,b\nand hypotenuse c", tag: "tikz" },
  { text: "sine and cosine on\n[-2pi, 2pi]", tag: "matplotlib" },
  { text: "binary search tree with\n5, 3, 7, 1, 4, 6, 8", tag: "graphviz" }
];

defineEmits<{
  (event: "pick", value: string): void;
  (event: "update:draft", value: string): void;
  (event: "submit", payload: { prompt: string; backend: string; maxTurns: number }): void;
}>();

defineProps<{
  draft: string;
  disabled?: boolean;
}>();
</script>

<style scoped>
.empty {
  display: grid;
  place-items: center;
  padding: 24px;
}

.inner {
  width: min(560px, 100%);
  display: grid;
  gap: 36px;
}

.hero-title {
  display: inline-flex;
  align-items: center;
  gap: 12px;
}

.hero h1 {
  margin: 0;
  font-family: "Newsreader", serif;
  font-size: 28px;
  font-weight: 500;
}

.hero p {
  margin: 12px 0 0;
  color: #888888;
  font-family: "Inter", sans-serif;
  font-size: 13px;
  line-height: 1.45;
  white-space: pre-line;
}

.examples {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.input-area {
  display: grid;
  gap: 14px;
}

.hint {
  margin: 0;
  font-family: "Inter", sans-serif;
  font-size: 12px;
  color: #cccccc;
}

@media (max-width: 900px) {
  .examples {
    grid-template-columns: 1fr;
  }
}
</style>
