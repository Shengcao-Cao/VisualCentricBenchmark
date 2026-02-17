export type BackendName = "auto" | "tikz" | "matplotlib" | "graphviz" | "unknown";
export type StepStatus = "running" | "done";

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
  input: string;
  status: StepStatus;
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

