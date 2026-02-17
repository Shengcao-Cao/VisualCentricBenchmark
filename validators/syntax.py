import ast
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from config import DOT_PATH, PDFLATEX_PATH, RENDER_TIMEOUT


@dataclass
class SyntaxReport:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def check_syntax(code: str, backend: str) -> SyntaxReport:
    if backend == "matplotlib":
        return _check_python(code)
    if backend == "tikz":
        return _check_tikz(code)
    if backend == "graphviz":
        return _check_graphviz(code)
    return SyntaxReport(valid=True)


# ── Python ────────────────────────────────────────────────────────────────────

def _check_python(code: str) -> SyntaxReport:
    try:
        ast.parse(code)
    except SyntaxError as exc:
        return SyntaxReport(
            valid=False,
            errors=[f"SyntaxError at line {exc.lineno}: {exc.msg}"],
        )
    return SyntaxReport(valid=True)


# ── TikZ / LaTeX ──────────────────────────────────────────────────────────────

def _check_tikz(code: str) -> SyntaxReport:
    """Compile in draft mode to catch errors without producing output."""
    from backends.tikz import _TIKZ_TEMPLATE  # avoid circular at module level

    if r"\documentclass" not in code:
        code = _TIKZ_TEMPLATE.replace("%BODY%", code)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        tex_file = tmpdir / "check.tex"
        tex_file.write_text(code, encoding="utf-8")

        try:
            result = subprocess.run(
                [
                    PDFLATEX_PATH,
                    "-interaction=nonstopmode",
                    "-draftmode",
                    "-output-directory",
                    str(tmpdir),
                    str(tex_file),
                ],
                capture_output=True,
                text=True,
                timeout=RENDER_TIMEOUT,
            )
        except FileNotFoundError:
            # pdflatex not available — skip check
            return SyntaxReport(valid=True, warnings=["pdflatex not found; skipping LaTeX syntax check"])
        except subprocess.TimeoutExpired:
            return SyntaxReport(valid=False, errors=["LaTeX syntax check timed out"])

        if result.returncode != 0:
            errors = _extract_errors(result.stdout + result.stderr)
            return SyntaxReport(valid=False, errors=errors)

    return SyntaxReport(valid=True)


def _extract_errors(log: str) -> list[str]:
    lines = log.splitlines()
    errors = []
    for i, line in enumerate(lines):
        if line.startswith("!"):
            block = lines[i : i + 5]
            errors.append("\n".join(block))
    return errors or [log[-1000:]]


# ── Graphviz / DOT ────────────────────────────────────────────────────────────

def _check_graphviz(code: str) -> SyntaxReport:
    with tempfile.TemporaryDirectory() as tmpdir:
        dot_file = Path(tmpdir) / "check.dot"
        dot_file.write_text(code, encoding="utf-8")

        try:
            result = subprocess.run(
                [DOT_PATH, "-Tsvg", "-o", str(Path(tmpdir) / "out.svg"), str(dot_file)],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except FileNotFoundError:
            return SyntaxReport(valid=True, warnings=["dot not found; skipping Graphviz syntax check"])
        except subprocess.TimeoutExpired:
            return SyntaxReport(valid=False, errors=["Graphviz syntax check timed out"])

        if result.returncode != 0:
            return SyntaxReport(valid=False, errors=[result.stderr.strip()])

    return SyntaxReport(valid=True)
