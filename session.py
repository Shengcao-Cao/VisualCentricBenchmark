"""Conversation session management for multi-turn dialogue."""
from __future__ import annotations

import json
import shutil
import sqlite3
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import cast

import config as cfg


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


@dataclass
class ConversationSession:
    """Holds all state for one user conversation."""

    id: str
    # Full Anthropic-format message history (user/assistant alternating)
    messages: list[dict[str, object]] = field(default_factory=list)
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
    def __init__(self) -> None:
        self._root_dir: Path = Path(cfg.BASE_DIR) / "sessions"
        self._db_path: Path = self._root_dir / "sessions.sqlite3"
        self._lock: threading.RLock = threading.RLock()

        self._root_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        _ = conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            _ = conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    messages_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_activity TEXT NOT NULL,
                    current_render_id TEXT
                )
                """
            )
            _ = conn.execute(
                """
                CREATE TABLE IF NOT EXISTS renders (
                    session_id TEXT NOT NULL,
                    render_id TEXT NOT NULL,
                    render_index INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (session_id, render_id),
                    UNIQUE (session_id, render_index),
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
                """
            )

    @staticmethod
    def _serialize_dt(value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()

    @staticmethod
    def _parse_dt(value: str) -> datetime:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    @staticmethod
    def _render_index(render_id: str) -> int | None:
        if render_id.startswith("v") and render_id[1:].isdigit():
            return int(render_id[1:])
        return None

    def _session_dir(self, session_id: str) -> Path:
        return self._root_dir / session_id

    def _renders_dir(self, session_id: str) -> Path:
        return self._session_dir(session_id) / "renders"

    def create(self) -> ConversationSession:
        session = ConversationSession(id=uuid.uuid4().hex)
        with self._lock:
            with self._connect() as conn:
                _ = conn.execute(
                    """
                    INSERT INTO sessions (id, messages_json, created_at, last_activity, current_render_id)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        session.id,
                        json.dumps(session.messages),
                        self._serialize_dt(session.created_at),
                        self._serialize_dt(session.last_activity),
                        session.current_render_id,
                    ),
                )
        return session

    def get(self, session_id: str) -> ConversationSession | None:
        with self._lock:
            with self._connect() as conn:
                row = cast(
                    tuple[str, str, str, str | None] | None,
                    conn.execute(
                    """
                    SELECT messages_json, created_at, last_activity, current_render_id
                    FROM sessions
                    WHERE id = ?
                    """,
                    (session_id,),
                    ).fetchone(),
                )
                if row is None:
                    return None

                messages_json, created_at_s, last_activity_s, current_render_id = row
                render_rows = cast(
                    list[tuple[str, str]],
                    conn.execute(
                    """
                    SELECT render_id, file_path
                    FROM renders
                    WHERE session_id = ?
                    ORDER BY render_index ASC
                    """,
                    (session_id,),
                    ).fetchall(),
                )

            renders: dict[str, bytes] = {}
            for render_id, file_path in render_rows:
                path = Path(file_path)
                if path.exists():
                    renders[render_id] = path.read_bytes()

            messages = cast(list[dict[str, object]], json.loads(messages_json))

            return ConversationSession(
                id=session_id,
                messages=messages,
                renders=renders,
                current_render_id=current_render_id,
                created_at=self._parse_dt(created_at_s),
                last_activity=self._parse_dt(last_activity_s),
            )

    def update(self, session: ConversationSession) -> None:
        session.touch()

        with self._lock:
            render_dir = self._renders_dir(session.id)
            render_dir.mkdir(parents=True, exist_ok=True)

            with self._connect() as conn:
                existing_render_rows = cast(
                    list[tuple[str]],
                    conn.execute(
                        "SELECT render_id FROM renders WHERE session_id = ?",
                        (session.id,),
                    ).fetchall(),
                )
                existing_render_ids = {
                    render_row[0]
                    for render_row in existing_render_rows
                }

                for render_id, image_bytes in session.renders.items():
                    if render_id in existing_render_ids:
                        continue

                    render_index = self._render_index(render_id)
                    if render_index is None:
                        continue

                    render_path = render_dir / f"{render_id}.png"
                    _ = render_path.write_bytes(image_bytes)
                    _ = conn.execute(
                        """
                        INSERT INTO renders (session_id, render_id, render_index, file_path, created_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            session.id,
                            render_id,
                            render_index,
                            str(render_path),
                            self._serialize_dt(_utcnow()),
                        ),
                    )

                _ = conn.execute(
                    """
                    UPDATE sessions
                    SET messages_json = ?,
                        created_at = ?,
                        last_activity = ?,
                        current_render_id = ?
                    WHERE id = ?
                    """,
                    (
                        json.dumps(session.messages),
                        self._serialize_dt(session.created_at),
                        self._serialize_dt(session.last_activity),
                        session.current_render_id,
                        session.id,
                    ),
                )

    def delete(self, session_id: str) -> None:
        with self._lock:
            with self._connect() as conn:
                _ = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            shutil.rmtree(self._session_dir(session_id), ignore_errors=True)

    def cleanup_expired(self) -> None:
        ttl = timedelta(seconds=cfg.SESSION_TTL_SECONDS)
        now = _utcnow()

        with self._lock:
            with self._connect() as conn:
                rows = cast(
                    list[tuple[str, str]],
                    conn.execute("SELECT id, last_activity FROM sessions").fetchall(),
                )

                expired_ids = [
                    session_row[0]
                    for session_row in rows
                    if now - self._parse_dt(session_row[1]) > ttl
                ]

                for session_id in expired_ids:
                    _ = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

            for session_id in expired_ids:
                shutil.rmtree(self._session_dir(session_id), ignore_errors=True)

    def __len__(self) -> int:
        with self._lock:
            with self._connect() as conn:
                row = cast(tuple[int] | None, conn.execute("SELECT COUNT(*) FROM sessions").fetchone())
        return int(row[0]) if row else 0
