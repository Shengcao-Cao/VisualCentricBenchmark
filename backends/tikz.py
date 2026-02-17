import io
import subprocess
import tempfile
from pathlib import Path

from backends.base import RenderResult
from config import PDFLATEX_PATH, RENDER_TIMEOUT

_TIKZ_TEMPLATE = r"""
\documentclass[tikz,border=10pt]{standalone}
\usepackage{tikz}
\usepackage{pgfplots}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{bm}
\usetikzlibrary{
    arrows.meta,
    shapes,
    shapes.geometric,
    positioning,
    calc,
    decorations.pathmorphing,
    decorations.markings,
    patterns,
    3d,
    matrix,
    cd
}
\pgfplotsset{compat=1.18}
\begin{document}
%BODY%
\end{document}
"""


def render_tikz(latex_source: str) -> RenderResult:
    if r"\documentclass" not in latex_source:
        latex_source = _TIKZ_TEMPLATE.replace("%BODY%", latex_source)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        tex_file = tmpdir / "diagram.tex"
        tex_file.write_text(latex_source, encoding="utf-8")

        try:
            result = subprocess.run(
                [
                    PDFLATEX_PATH,
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-output-directory",
                    str(tmpdir),
                    str(tex_file),
                ],
                capture_output=True,
                text=True,
                timeout=RENDER_TIMEOUT,
            )
        except FileNotFoundError:
            return RenderResult(
                success=False,
                error="pdflatex not found. Install TeX Live or MiKTeX and ensure pdflatex is on PATH.",
                backend="tikz",
                source_code=latex_source,
            )
        except subprocess.TimeoutExpired:
            return RenderResult(
                success=False,
                error=f"pdflatex timed out after {RENDER_TIMEOUT}s",
                backend="tikz",
                source_code=latex_source,
            )

        pdf_file = tmpdir / "diagram.pdf"
        if not pdf_file.exists():
            return RenderResult(
                success=False,
                stderr=result.stderr,
                error=_extract_latex_error(result.stdout + result.stderr),
                backend="tikz",
                source_code=latex_source,
            )

        try:
            from pdf2image import convert_from_path

            images = convert_from_path(str(pdf_file), dpi=200, first_page=1, last_page=1)
            if not images:
                return RenderResult(
                    success=False,
                    error="pdf2image returned no pages",
                    backend="tikz",
                    source_code=latex_source,
                )
            buf = io.BytesIO()
            images[0].save(buf, format="PNG")
            return RenderResult(
                success=True,
                image_bytes=buf.getvalue(),
                format="png",
                stdout=result.stdout,
                stderr=result.stderr,
                backend="tikz",
                source_code=latex_source,
            )
        except Exception as e:
            return RenderResult(
                success=False,
                error=f"PDF-to-PNG conversion failed: {e}",
                stderr=result.stderr,
                backend="tikz",
                source_code=latex_source,
            )


def _extract_latex_error(log: str) -> str:
    """Pull the first LaTeX error line from a pdflatex log."""
    lines = log.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("!"):
            context = lines[i : i + 5]
            return "\n".join(context)
    return log[-2000:] if len(log) > 2000 else log
