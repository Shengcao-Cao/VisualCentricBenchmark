<template>
  <div class="steps">
    <div class="label mono">PROCESS</div>
    <div v-for="step in steps" :key="step.id" class="step-container">
      <div class="row clickable" @click="toggleExpand(step.id)">
        <span>{{ step.label }}</span>
        <span class="status-wrap">
          <AppIcon v-if="step.stepStatus === 'done'" name="check" :size="10" color="#0D6E6E" />
          <AppIcon v-else name="loader" :size="10" color="#0D6E6E" :spin="true" />
          <span class="mono status">{{ step.stepStatus }}</span>
          <AppIcon :name="expandedSteps.has(step.id) ? 'chevron-down' : 'triangle-right'" :size="10" color="#999" />
        </span>
      </div>
      <div v-if="expandedSteps.has(step.id)" class="details">
        <div v-if="step.tool" class="detail-row">
          <span class="detail-label">Tool:</span>
          <span class="detail-value mono">{{ step.tool }}</span>
        </div>
        <div v-if="step.toolUseId" class="detail-row">
          <span class="detail-label">Tool Use ID:</span>
          <span class="detail-value mono">{{ step.toolUseId }}</span>
        </div>
        <div v-if="step.durationMs !== null && step.durationMs !== undefined" class="detail-row">
          <span class="detail-label">Duration:</span>
          <span class="detail-value mono">{{ step.durationMs }}ms</span>
        </div>
        <div v-if="step.status" class="detail-row">
          <span class="detail-label">Status:</span>
          <span class="detail-value mono" :class="{ 'error': step.status === 'error' }">{{ step.status }}</span>
        </div>

        <div v-if="step.inputSummary || step.inputFull" class="detail-section">
          <div class="detail-header">
            <span class="detail-label">Input:</span>
            <span v-if="step.inputTruncated" class="truncated-badge">truncated</span>
            <button class="copy-btn" @click.stop="copyToClipboard(formatDisplayText(step.inputFull ?? step.inputSummary))" title="Copy input">
              <AppIcon name="share-2" :size="12" color="#666" />
            </button>
          </div>
          <div class="code-block">
            <pre class="mono">{{ formatDisplayText(step.inputFull ?? step.inputSummary) }}</pre>
          </div>
        </div>

        <div v-if="step.resultSummary || step.resultText || step.error" class="detail-section">
          <div class="detail-header">
            <span class="detail-label">Output:</span>
            <span v-if="step.resultTruncated" class="truncated-badge">truncated</span>
            <button v-if="step.resultSummary || step.resultText" class="copy-btn" @click.stop="copyToClipboard(formatDisplayText(step.resultText ?? step.resultSummary))" title="Copy output">
              <AppIcon name="share-2" :size="12" color="#666" />
            </button>
          </div>
          <div class="code-block">
            <pre v-if="step.resultText || step.resultSummary" class="mono">{{ formatDisplayText(step.resultText ?? step.resultSummary) }}</pre>
            <div v-if="step.error" class="error-block">
              <div v-if="step.error.name" class="error-line mono">{{ step.error.name }}</div>
              <div v-if="step.error.message" class="error-line mono">{{ step.error.message }}</div>
              <div v-if="step.error.stack" class="error-stack mono">{{ step.error.stack }}</div>
            </div>
          </div>
        </div>

        <div v-if="step.artifacts" class="detail-row">
          <span class="detail-label">Artifacts:</span>
          <span class="detail-value mono">{{ step.artifacts.has_binary ? 'has binary' : 'text only' }} ({{ step.artifacts.omitted.length }} omitted)</span>
        </div>

        <div v-if="step.redaction" class="detail-row">
          <span class="detail-label">Redaction:</span>
          <span class="detail-value mono">{{ step.redaction.mode }} ({{ step.redaction.applied ? 'applied' : 'not applied' }})</span>
        </div>

        <div v-if="step.size" class="detail-row">
          <span class="detail-label">Size:</span>
          <span class="detail-value mono">{{ step.size.event_bytes }} bytes</span>
          <span v-if="step.size.event_truncated" class="truncated-badge">truncated</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { ProcessStep } from "../../types/domain";
import AppIcon from "../ui/AppIcon.vue";

defineProps<{ steps: ProcessStep[] }>();

const expandedSteps = ref<Set<string>>(new Set());

function toggleExpand(stepId: string): void {
  if (expandedSteps.value.has(stepId)) {
    expandedSteps.value.delete(stepId);
  } else {
    expandedSteps.value.add(stepId);
  }
}

async function copyToClipboard(text: string | null | undefined): Promise<void> {
  if (!text) return;
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
    } else {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
    }
  } catch (err) {
    console.error('Failed to copy to clipboard:', err);
  }
}

function formatDisplayText(text: string | null | undefined): string {
  if (!text) return '';
  
  // Try to parse as JSON
  try {
    const parsed = JSON.parse(text);
    // Re-stringify with 2-space indentation for pretty display
    return JSON.stringify(parsed, null, 2);
  } catch {
    // Not valid JSON, return as-is
    return text;
  }
}
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

.step-container {
  margin-bottom: 4px;
}

.row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 11px;
  color: #666;
  padding: 2px 0;
}

.row.clickable {
  cursor: pointer;
  user-select: none;
}

.row.clickable:hover {
  background-color: #f5f5f5;
  border-radius: 4px;
  padding: 2px 6px;
  margin: 0 -6px;
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

.details {
  margin-top: 8px;
  padding: 12px;
  background-color: #fafafa;
  border-radius: 6px;
  border: 1px solid #e8e8e8;
}

.detail-row {
  display: flex;
  gap: 8px;
  font-size: 11px;
  margin-bottom: 6px;
  align-items: center;
}

.detail-section {
  margin-top: 10px;
  margin-bottom: 10px;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.detail-label {
  font-size: 10px;
  color: #999;
  font-weight: 500;
}

.detail-value {
  font-size: 11px;
  color: #333;
}

.detail-value.error {
  color: #d32f2f;
}

.truncated-badge {
  font-size: 9px;
  color: #f57c00;
  background-color: #fff3e0;
  padding: 2px 6px;
  border-radius: 3px;
}

.copy-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: auto;
}

.copy-btn:hover {
  background-color: #e8e8e8;
  border-radius: 3px;
}

.code-block {
  background-color: #f5f5f5;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 10px;
  max-height: 300px;
  overflow-y: auto;
}

.code-block pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 10px;
  color: #333;
  line-height: 1.4;
}

.error-block {
  margin-top: 8px;
}

.error-line {
  font-size: 10px;
  color: #d32f2f;
  margin-bottom: 4px;
}

.error-stack {
  font-size: 9px;
  color: #666;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
