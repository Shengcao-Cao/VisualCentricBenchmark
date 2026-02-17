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

    <p v-if="turn.reply" class="reply">{{ turn.reply }}</p>

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
import type { ThreadTurn } from "../../types/domain";
import DownloadButton from "./DownloadButton.vue";
import ProcessSteps from "./ProcessSteps.vue";
import RenderPreview from "./RenderPreview.vue";
import AppIcon from "../ui/AppIcon.vue";

defineProps<{ turn: ThreadTurn }>();
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
  padding: 0 14px 10px;
  color: #333;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
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
