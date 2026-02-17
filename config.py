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

# Claude model
DEFAULT_MODEL = os.environ.get("DIAGRAM_MODEL", "claude-opus-4-6")

# Agent settings
MAX_REPAIR_ATTEMPTS = int(os.environ.get("MAX_REPAIR_ATTEMPTS", "3"))
VISUAL_SCORE_THRESHOLD = float(os.environ.get("VISUAL_SCORE_THRESHOLD", "7.0"))
MAX_AGENT_TURNS = int(os.environ.get("MAX_AGENT_TURNS", "20"))

# Timeouts in seconds
RENDER_TIMEOUT = int(os.environ.get("RENDER_TIMEOUT", "60"))
SANDBOX_TIMEOUT = int(os.environ.get("SANDBOX_TIMEOUT", "30"))
