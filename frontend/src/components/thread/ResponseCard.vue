<template>
  <section class="response">
    <div class="header">
      <div class="left mono">
        <AppIcon name="aperture" :size="12" />
        <span>RESPONSE</span>
      </div>
      <div class="right mono">
        <span class="chip">{{ turn.backend }}</span>
        <span class="chip score" v-if="turn.score !== null">
          <AppIcon name="check" :size="9" color="#0D6E6E" />
          <span>{{ turn.score.toFixed(1) }} / 10</span>
        </span>
      </div>
    </div>

    <div v-if="turn.reply" class="reply markdown" v-html="replyHtml" />

    <ProcessSteps :steps="turn.steps" />
    <RenderPreview :render-url="turn.renderUrl" />

    <footer class="footer">
      <div class="meta mono">
        <span>{{ turn.steps.length }} steps</span>
        <span>·</span>
        <span>{{ turn.isStreaming ? "streaming" : "done" }}</span>
      </div>
      <DownloadButton :render-url="turn.renderUrl" :render-id="turn.renderId" />
    </footer>

    <p v-if="turn.error" class="error mono">{{ turn.error }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { ThreadTurn } from "../../types/domain";
import { markdownToHtml } from "../../utils/markdown";
import DownloadButton from "./DownloadButton.vue";
import ProcessSteps from "./ProcessSteps.vue";
import RenderPreview from "./RenderPreview.vue";
import AppIcon from "../ui/AppIcon.vue";

const props = defineProps<{ turn: ThreadTurn }>();
const replyHtml = computed(() => markdownToHtml(props.turn.reply));
</script>

<style scoped>
.response {
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  background: #fff;
  overflow: hidden;
}

.header {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 14px;
}

.left {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #0d6e6e;
  font-size: 10px;
  letter-spacing: 1.5px;
}

.right {
  display: flex;
  gap: 8px;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #f0f0f0;
  border-radius: 4px;
  padding: 2px 8px;
  color: #666;
  font-size: 10px;
}

.chip.score {
  background: #f0faf9;
  color: #0d6e6e;
}

.reply {
  margin: 0;
  padding: 0 14px 6px;
  color: #222;
  font-family: "Georgia", "Iowan Old Style", "Palatino Linotype", "Times New Roman", serif;
  font-size: 16px;
  line-height: 1.47;
  letter-spacing: 0.01em;
}

.markdown :deep(p) {
  margin: 0 0 5px;
}

.markdown :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown :deep(h1),
.markdown :deep(h2),
.markdown :deep(h3),
.markdown :deep(h4),
.markdown :deep(h5),
.markdown :deep(h6) {
  margin: 0 0 6px;
  line-height: 1.15;
  color: #111;
  font-family: "Inter", "Segoe UI", sans-serif;
  letter-spacing: -0.01em;
  font-weight: 650;
}

.markdown :deep(h1) {
  font-size: 1.55em;
}

.markdown :deep(h2) {
  font-size: 1.35em;
}

.markdown :deep(h3) {
  font-size: 1.2em;
}

.markdown :deep(ul),
.markdown :deep(ol) {
  margin: 0 0 5px;
  padding-left: 16px;
}

.markdown :deep(li) {
  margin: 0 0 1px;
}

.markdown :deep(blockquote) {
  margin: 0 0 5px;
  padding-left: 8px;
  border-left: 3px solid #e5e5e5;
  color: #5c5c5c;
}

.markdown :deep(code) {
  font-family: "JetBrains Mono", "Cascadia Code", "Consolas", monospace;
  font-size: 0.9em;
  background: #f4f6f8;
  border-radius: 4px;
  padding: 1px 5px;
}

.markdown :deep(pre) {
  margin: 0 0 5px;
  padding: 8px 10px;
  background: #0f1720;
  color: #eaf1f8;
  border-radius: 8px;
  overflow: auto;
  line-height: 1.28;
}

.markdown :deep(pre code) {
  background: transparent;
  border-radius: 0;
  padding: 0;
  color: inherit;
}

.markdown :deep(a) {
  color: #0d6e6e;
}

.footer {
  border-top: 1px solid #e5e5e5;
  padding: 8px 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.meta {
  display: flex;
  gap: 6px;
  color: #999;
  font-size: 10px;
}

.error {
  margin: 0;
  padding: 8px 14px 12px;
  color: #b42318;
  font-size: 11px;
}
</style>
