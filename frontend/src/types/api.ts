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
}

export interface ToolResultPayload {
  tool: string;
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

