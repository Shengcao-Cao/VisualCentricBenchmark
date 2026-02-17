<template>
  <button class="download" type="button" :disabled="!renderUrl" @click="onDownload">Download</button>
</template>

<script setup lang="ts">
const props = defineProps<{
  renderUrl: string | null;
  renderId: string | null;
}>();

function onDownload(): void {
  if (!props.renderUrl) return;
  const anchor = document.createElement("a");
  anchor.href = props.renderUrl;
  anchor.download = `${props.renderId ?? "diagram"}.png`;
  anchor.click();
}
</script>

<style scoped>
.download {
  height: 24px;
  border: 1px solid #e5e5e5;
  border-radius: 4px;
  background: #fff;
  padding: 0 10px;
  cursor: pointer;
}
</style>

