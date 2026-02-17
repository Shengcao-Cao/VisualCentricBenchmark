import { getApiBase } from "./http";
import type { SseEventType } from "../../types/api";

export interface ParsedSseEvent {
  event: SseEventType;
  data: unknown;
}

export async function streamSessionMessage(
  sessionId: string,
  content: string,
  onEvent: (event: ParsedSseEvent) => Promise<void> | void
): Promise<void> {
  const response = await fetch(`${getApiBase()}/sessions/${sessionId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content })
  });

  if (!response.ok || !response.body) {
    const text = await response.text();
    throw new Error(`SSE request failed: ${response.status} ${text}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";

    for (const chunk of chunks) {
      const lines = chunk.split("\n");
      let eventName = "";
      const dataLines: string[] = [];

      for (const line of lines) {
        if (line.startsWith("event:")) {
          eventName = line.slice(6).trim();
        } else if (line.startsWith("data:")) {
          dataLines.push(line.slice(5).trim());
        }
      }

      if (!eventName || dataLines.length === 0) continue;
      const rawData = dataLines.join("\n");
      const data = JSON.parse(rawData);
      await onEvent({ event: eventName as SseEventType, data });
    }
  }
}

