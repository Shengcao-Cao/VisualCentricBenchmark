import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from backends.base import RenderResult
from config import SANDBOX_TIMEOUT

_SANDBOX_RUNNER = Path(__file__).parent.parent / "sandbox" / "matplotlib_runner.py"


def render_matplotlib(python_source: str) -> RenderResult:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        script_path = tmpdir / "diagram.py"
        output_path = tmpdir / "diagram.png"

        sanitized = _sanitize(python_source)
        script_path.write_text(sanitized, encoding="utf-8")

        env = {**os.environ, "DIAGRAM_OUTPUT_PATH": str(output_path)}

        try:
            result = subprocess.run(
                [sys.executable, str(_SANDBOX_RUNNER), str(script_path)],
                capture_output=True,
                text=True,
                timeout=SANDBOX_TIMEOUT,
                env=env,
            )
        except subprocess.TimeoutExpired:
            return RenderResult(
                success=False,
                error=f"Matplotlib execution timed out after {SANDBOX_TIMEOUT}s",
                backend="matplotlib",
                source_code=python_source,
            )

        if result.returncode != 0:
            return RenderResult(
                success=False,
                stderr=result.stderr,
                error=result.stderr.strip() or "Script exited with non-zero status",
                backend="matplotlib",
                source_code=python_source,
            )

        if not output_path.exists():
            return RenderResult(
                success=False,
                error="Script ran but produced no output file. Ensure the code calls plt.savefig().",
                stdout=result.stdout,
                backend="matplotlib",
                source_code=python_source,
            )

        return RenderResult(
            success=True,
            image_bytes=output_path.read_bytes(),
            format="png",
            stdout=result.stdout,
            stderr=result.stderr,
            backend="matplotlib",
            source_code=python_source,
        )


def _sanitize(code: str) -> str:
    """Strip interactive calls and ensure Agg backend + savefig."""
    # Force non-interactive backend before any matplotlib import
    header = 'import matplotlib\nmatplotlib.use("Agg")\n'

    # Remove plt.show() and pyplot.show()
    code = re.sub(r"\b(?:plt|pyplot)\.show\(\)", "", code)

    # Check if code already saves the figure
    has_savefig = bool(re.search(r"savefig\s*\(", code))

    footer = ""
    if not has_savefig:
        footer = (
            "\nimport os as _os\n"
            "import matplotlib.pyplot as _plt\n"
            '_plt.savefig(_os.environ.get("DIAGRAM_OUTPUT_PATH", "output.png"), '
            'dpi=150, bbox_inches="tight")\n'
        )

    return header + code + footer
