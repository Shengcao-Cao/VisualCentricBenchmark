import { fetchRenderBlob } from "../services/api/sessions.api";

const cache = new Map<string, string>();

export function useRenderImage() {
  async function getRenderUrl(sessionId: string, renderId: string): Promise<string> {
    const cacheKey = `${sessionId}:${renderId}`;
    const cached = cache.get(cacheKey);
    if (cached) return cached;

    const blob = await fetchRenderBlob(sessionId, renderId);
    const url = URL.createObjectURL(blob);
    cache.set(cacheKey, url);
    return url;
  }

  return { getRenderUrl };
}

