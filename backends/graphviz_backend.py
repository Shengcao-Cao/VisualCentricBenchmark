import subprocess
import tempfile
from pathlib import Path
from typing import Literal

from backends.base import RenderResult
from config import DOT_PATH, RENDER_TIMEOUT

Engine = Literal["dot", "neato", "circo", "fdp", "sfdp", "twopi"]


def render_graphviz(dot_source: str, engine: Engine = "dot") -> RenderResult:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        dot_file = tmpdir / "diagram.dot"
        png_file = tmpdir / "diagram.png"
        dot_file.write_text(dot_source, encoding="utf-8")

        # Resolve engine binary: prefer full path if DOT_PATH points to a dir
        binary = _resolve_engine(engine)

        try:
            result = subprocess.run(
                [binary, "-Tpng", "-o", str(png_file), str(dot_file)],
                capture_output=True,
                text=True,
                timeout=RENDER_TIMEOUT,
            )
        except FileNotFoundError:
            return RenderResult(
                success=False,
                error=f"Graphviz '{engine}' not found. Install Graphviz and ensure it is on PATH.",
                backend="graphviz",
                source_code=dot_source,
            )
        except subprocess.TimeoutExpired:
            return RenderResult(
                success=False,
                error=f"Graphviz timed out after {RENDER_TIMEOUT}s",
                backend="graphviz",
                source_code=dot_source,
            )

        if result.returncode != 0 or not png_file.exists():
            return RenderResult(
                success=False,
                stderr=result.stderr,
                error=result.stderr.strip() or "Graphviz failed with no error message",
                backend="graphviz",
                source_code=dot_source,
            )

        return RenderResult(
            success=True,
            image_bytes=png_file.read_bytes(),
            format="png",
            stdout=result.stdout,
            stderr=result.stderr,
            backend="graphviz",
            source_code=dot_source,
        )


def _resolve_engine(engine: str) -> str:
    """Return the binary name for the given engine, using DOT_PATH as hint."""
    import os

    dot_path = DOT_PATH
    # If DOT_PATH points to a directory, build the full path
    if os.path.isdir(dot_path):
        return str(Path(dot_path) / engine)
    # If DOT_PATH is the dot binary itself, derive siblings from its directory
    if os.path.basename(dot_path).lower() in ("dot", "dot.exe"):
        return str(Path(dot_path).parent / engine)
    return engine
