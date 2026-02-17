import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"

OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# External tool paths (override via environment variables)
PDFLATEX_PATH = os.environ.get("PDFLATEX_PATH", "pdflatex")
DOT_PATH = os.environ.get("DOT_PATH", "dot")

# API provider: "anthropic" (default) or "openai" (any OpenAI-compatible endpoint)
API_PROVIDER = os.environ.get("API_PROVIDER", "anthropic").lower()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "")

# Model
DEFAULT_MODEL = os.environ.get("DIAGRAM_MODEL", "claude-opus-4-6")

# Agent settings
MAX_REPAIR_ATTEMPTS = int(os.environ.get("MAX_REPAIR_ATTEMPTS", "3"))
VISUAL_SCORE_THRESHOLD = float(os.environ.get("VISUAL_SCORE_THRESHOLD", "7.0"))
MAX_AGENT_TURNS = int(os.environ.get("MAX_AGENT_TURNS", "20"))

# Timeouts in seconds
RENDER_TIMEOUT = int(os.environ.get("RENDER_TIMEOUT", "60"))
SANDBOX_TIMEOUT = int(os.environ.get("SANDBOX_TIMEOUT", "30"))

# Session / server settings
SESSION_TTL_SECONDS = int(os.environ.get("SESSION_TTL_SECONDS", "3600"))
MAX_SESSIONS = int(os.environ.get("MAX_SESSIONS", "100"))
SERVER_HOST = os.environ.get("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.environ.get("SERVER_PORT", "8000"))
