export type BackendName = "auto" | "tikz" | "matplotlib" | "graphviz" | "unknown";
export type StepStatus = "running" | "done";

export interface StepRedaction {
  mode: "stream" | "persist";
  applied: boolean;
  rules: string[];
}

export interface StepSize {
  event_bytes: number;
  event_truncated: boolean;
}

export interface StepError {
  name: string | null;
  message: string | null;
  stack: string | null;
  stack_truncated: boolean;
}

export interface StepArtifacts {
  has_binary: boolean;
  omitted: { kind: string; size_bytes: number | null; reason: string }[];
}

export interface SessionEntry {
  id: string;
  title: string;
  backend: BackendName;
  exchanges: number;
  lastActiveLabel: string;
}

export interface ProcessStep {
  id: string;
  tool: string;
  label: string;
  toolUseId?: string | null;
  inputSummary: string;
  inputFull?: string | null;
  inputFullSizeBytes?: number | null;
  inputTruncated?: boolean;
  resultSummary?: string | null;
  resultText?: string | null;
  resultTextSizeBytes?: number | null;
  resultTruncated?: boolean;
  status?: "ok" | "error" | null;
  startedAtMs?: number | null;
  endedAtMs?: number | null;
  durationMs?: number | null;
  redaction?: StepRedaction;
  size?: StepSize;
  artifacts?: StepArtifacts | null;
  error?: StepError | null;
  stepStatus: StepStatus;
}

export interface ThreadTurn {
  id: string;
  prompt: string;
  reply: string;
  renderId: string | null;
  renderUrl: string | null;
  backend: BackendName;
  score: number | null;
  passed: boolean | null;
  issues: string[];
  suggestions: string[];
  steps: ProcessStep[];
  error: string | null;
  isStreaming: boolean;
  createdAt: number;
}

