"""Conversation session management for multi-turn dialogue."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import config as cfg


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


@dataclass
class ConversationSession:
    """Holds all state for one user conversation."""

    id: str
    # Full Anthropic-format message history (user/assistant alternating)
    messages: list[dict] = field(default_factory=list)
    # Render history: render_id ("v1", "v2", …) → PNG bytes
    renders: dict[str, bytes] = field(default_factory=dict)
    current_render_id: str | None = None
    created_at: datetime = field(default_factory=_utcnow)
    last_activity: datetime = field(default_factory=_utcnow)

    # ── Render helpers ────────────────────────────────────────────────────────

    def store_render(self, image_bytes: bytes) -> str:
        """Persist a new render and return its ID."""
        render_id = f"v{len(self.renders) + 1}"
        self.renders[render_id] = image_bytes
        self.current_render_id = render_id
        return render_id

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def touch(self) -> None:
        self.last_activity = _utcnow()

    @property
    def is_expired(self) -> bool:
        ttl = timedelta(seconds=cfg.SESSION_TTL_SECONDS)
        return _utcnow() - self.last_activity > ttl


class SessionStore:
    """In-memory session store (swap for Redis/DB as needed)."""

    def __init__(self) -> None:
        self._sessions: dict[str, ConversationSession] = {}

    def create(self) -> ConversationSession:
        session = ConversationSession(id=uuid.uuid4().hex)
        self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> ConversationSession | None:
        return self._sessions.get(session_id)

    def update(self, session: ConversationSession) -> None:
        session.touch()
        self._sessions[session.id] = session

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def cleanup_expired(self) -> None:
        expired = [sid for sid, s in self._sessions.items() if s.is_expired]
        for sid in expired:
            del self._sessions[sid]

    def __len__(self) -> int:
        return len(self._sessions)
