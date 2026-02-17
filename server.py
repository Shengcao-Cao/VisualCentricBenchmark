"""FastAPI server exposing the diagram agent as a dialogue API with SSE streaming.

Start with:
    uv run uvicorn server:app --host 127.0.0.1 --port 8000 --reload

Endpoints
---------
POST   /sessions                              Create a new conversation session
POST   /sessions/{id}/messages               Send a user message; returns SSE stream
GET    /sessions/{id}/renders/{render_id}    Fetch a rendered PNG image
GET    /sessions/{id}                        Get session metadata
DELETE /sessions/{id}                        Delete a session

SSE event types (on POST /sessions/{id}/messages)
--------------------------------------------------
text_delta      {"delta": "..."}
tool_start      {"tool": "render_matplotlib", "input": "..."}
tool_result     {"tool": "render_matplotlib"}
render_ready    {"render_id": "v1", "backend": "matplotlib"}
validate_result {"render_id": "v1", "score": 8.5, "passed": true, "issues": [...], "suggestions": [...]}
turn_complete   {"reply": "...", "render_id": "v1" | null}
error           {"message": "..."}
"""
from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

import config as cfg
from agent import run_turn_stream
from session import SessionStore

logger = logging.getLogger(__name__)

# ── Singleton session store ───────────────────────────────────────────────────

store = SessionStore()


# ── Periodic cleanup ──────────────────────────────────────────────────────────

async def _cleanup_loop() -> None:
    while True:
        await asyncio.sleep(300)  # every 5 minutes
        store.cleanup_expired()
        logger.debug("Session cleanup ran; active sessions: %d", len(store))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    task = asyncio.create_task(_cleanup_loop())
    yield
    task.cancel()


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="VisualCentricBenchmark API",
    description="Diagram generation agent with streaming dialogue support.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / response models ─────────────────────────────────────────────────

class MessageRequest(BaseModel):
    content: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/sessions", status_code=201)
async def create_session():
    """Create a new conversation session and return its ID."""
    if len(store) >= cfg.MAX_SESSIONS:
        store.cleanup_expired()
        if len(store) >= cfg.MAX_SESSIONS:
            raise HTTPException(status_code=503, detail="Session limit reached. Try again later.")
    session = store.create()
    return {"session_id": session.id}


@app.post("/sessions/{session_id}/messages")
async def send_message(session_id: str, body: MessageRequest):
    """Send a user message and stream the agent's response as SSE.

    The response is a ``text/event-stream`` where each frame is::

        event: <event_type>
        data: <json_payload>

    See module docstring for the list of event types.
    """
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    async def event_stream():
        try:
            async for event_type, payload in run_turn_stream(session, body.content):
                # Persist session immediately before yielding render_ready so
                # an immediate GET /renders/{render_id} will find the render.
                if event_type == "render_ready":
                    await asyncio.to_thread(store.update, session)
                yield f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"
        except Exception as exc:
            logger.exception("Error in agent turn for session %s", session_id)
            yield f"event: error\ndata: {json.dumps({'message': str(exc)})}\n\n"
        finally:
            store.update(session)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )


@app.get("/sessions/{session_id}/renders/{render_id}")
async def get_render(session_id: str, render_id: str):
    """Return the PNG image for a specific render."""
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    image_bytes = session.renders.get(render_id)
    if image_bytes is None:
        raise HTTPException(status_code=404, detail=f"Render '{render_id}' not found.")
    return Response(content=image_bytes, media_type="image/png")


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Return metadata about a session (no image bytes)."""
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {
        "id": session.id,
        "created_at": session.created_at.isoformat(),
        "last_activity": session.last_activity.isoformat(),
        "message_count": len(session.messages),
        "render_ids": list(session.renders.keys()),
        "current_render_id": session.current_render_id,
    }


@app.delete("/sessions/{session_id}", status_code=204)
async def delete_session(session_id: str):
    """Delete a session and free its memory."""
    store.delete(session_id)


# ── Dev entry-point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host=cfg.SERVER_HOST,
        port=cfg.SERVER_PORT,
        reload=True,
    )
