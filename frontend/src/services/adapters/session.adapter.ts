import type { SessionInfoResponse } from "../../types/api";
import type { SessionEntry } from "../../types/domain";
import { toRelativeLabel } from "../../utils/time";

export function toSessionEntry(dto: SessionInfoResponse): SessionEntry {
  return {
    id: dto.id,
    title: `Session ${dto.id.slice(0, 6)}`,
    backend: "auto",
    exchanges: Math.floor(dto.message_count / 2),
    lastActiveLabel: toRelativeLabel(dto.last_activity)
  };
}

