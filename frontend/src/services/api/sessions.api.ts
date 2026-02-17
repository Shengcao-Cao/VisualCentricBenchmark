import { fetchJson, getApiBase } from "./http";
import type { CreateSessionResponse, SessionInfoResponse } from "../../types/api";

export async function createSession(): Promise<CreateSessionResponse> {
  return fetchJson<CreateSessionResponse>("/sessions", { method: "POST" });
}

export async function getSession(sessionId: string): Promise<SessionInfoResponse> {
  return fetchJson<SessionInfoResponse>(`/sessions/${sessionId}`, { method: "GET" });
}

export async function deleteSession(sessionId: string): Promise<void> {
  await fetchJson<void>(`/sessions/${sessionId}`, { method: "DELETE" });
}

export async function fetchRenderBlob(sessionId: string, renderId: string): Promise<Blob> {
  const response = await fetch(`${getApiBase()}/sessions/${sessionId}/renders/${renderId}`);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Failed to fetch render ${renderId}: ${response.status} ${text}`);
  }
  return response.blob();
}

