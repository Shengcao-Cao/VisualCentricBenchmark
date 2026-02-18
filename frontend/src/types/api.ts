export interface CreateSessionResponse {
  session_id: string;
}

export interface SessionInfoResponse {
  id: string;
  created_at: string;
  last_activity: string;
  message_count: number;
  render_ids: string[];
  current_render_id: string | null;
}

export type SseEventType =
  | "text_delta"
  | "tool_start"
  | "tool_result"
  | "render_ready"
  | "validate_result"
  | "turn_complete"
  | "error";

export interface ToolStartPayload {
  tool: string;
  input: string;
  trace_v?: number;
  tool_use_id?: string;
  ts_ms?: number;
  seq?: number;
  input_full?: string | null;
  input_full_size_bytes?: number | null;
  input_truncated?: boolean;
  redaction?: { mode: "stream" | "persist"; applied: boolean; rules: string[] };
  size?: { event_bytes: number; event_truncated: boolean };
}

export interface ToolResultPayload {
  tool: string;
  trace_v?: number;
  tool_use_id?: string;
  ts_ms?: number;
  seq?: number;
  status?: "ok" | "error";
  duration_ms?: number | null;
  result_summary?: string | null;
  result_text?: string | null;
  result_text_size_bytes?: number | null;
  result_truncated?: boolean;
  error?: {
    name: string | null;
    message: string | null;
    stack: string | null;
    stack_truncated: boolean;
  } | null;
  artifacts?: {
    has_binary: boolean;
    omitted: { kind: string; size_bytes: number | null; reason: string }[];
  } | null;
  redaction?: { mode: "stream" | "persist"; applied: boolean; rules: string[] };
  size?: { event_bytes: number; event_truncated: boolean };
}

export interface RenderReadyPayload {
  render_id: string;
  backend: string;
}

export interface ValidateResultPayload {
  render_id: string;
  score: number;
  passed: boolean;
  issues: string[];
  suggestions: string[];
}

export interface TurnCompletePayload {
  reply: string;
  render_id: string | null;
}

export interface ErrorPayload {
  message: string;
}

export interface TextDeltaPayload {
  delta: string;
}

