# VisualCentricBenchmark

A diagram agent that generates textbook-quality math diagrams using TikZ, Matplotlib, and Graphviz.

---

## Getting Started

### Prerequisites

| Tool | Required for | Install |
|---|---|---|
| Python ≥ 3.11 | everything | [python.org](https://python.org) |
| [uv](https://docs.astral.sh/uv/) | package management | `pip install uv` |
| pdflatex (TeX Live / MiKTeX) | TikZ diagrams | [tug.org/texlive](https://tug.org/texlive/) |
| [Graphviz](https://graphviz.org/download/) | graph/tree diagrams | system package manager |

Matplotlib diagrams work out of the box — no external binaries needed.

### Install

```bash
git clone <repo>
cd VisualCentricBenchmark
uv sync
```

### Set your API key

```bash
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY=sk-ant-...
```

`config.py` loads `.env` automatically via `python-dotenv` — no shell sourcing needed. Alternatively, export directly:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

---

## Usage

```bash
uv run agent.py "<description>"
uv run agent.py "<description>" --output <filename>
uv run agent.py "<description>" --model <model-id>
uv run agent.py "<description>" --max-turns <n>
```

### Examples

```bash
# Geometric diagram (TikZ)
uv run agent.py "a right triangle with legs labeled a, b and hypotenuse c, with a small square at the right angle"

# Function plot (Matplotlib)
uv run agent.py "sine and cosine plotted on [-2pi, 2pi] with a legend" --output trig.png

# Graph / tree (Graphviz)
uv run agent.py "binary search tree containing 5, 3, 7, 1, 4, 6, 8" --output bst.png

# Finite automaton (Graphviz)
uv run agent.py "DFA that accepts strings ending in 01 over alphabet {0,1}" --output dfa.png

# Commutative diagram (TikZ)
uv run agent.py "commutative square with maps f, g, h, k between objects A, B, C, D"

# Use a cheaper model
uv run agent.py "unit circle with labeled angles" --model claude-sonnet-4-5-20250929
```

Diagrams are saved to `output/` by default. Progress is printed to stderr; the final JSON result is printed to stdout.

### Output

```jsonc
{
  "status": "complete",        // "complete" | "max_turns" | "error"
  "message": "...",            // agent's closing message
  "output": "output/bst.png"  // path to saved file, or null
}
```

Exit code `0` on success, `1` on failure.

---

## Configuration

All settings are controlled by environment variables. Copy `.env.example` to `.env` and edit as needed.

### Required

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key ([console.anthropic.com](https://console.anthropic.com)) |

### Model

| Variable | Default | Description |
|---|---|---|
| `DIAGRAM_MODEL` | `claude-opus-4-6` | Claude model for the agent loop and visual validation. Use `claude-sonnet-4-5-20250929` for lower cost. |

### External binary paths

Only set these if the binaries are not on your `PATH`.

| Variable | Default | Description |
|---|---|---|
| `PDFLATEX_PATH` | `pdflatex` | Path to the `pdflatex` executable. Required for TikZ diagrams. |
| `DOT_PATH` | `dot` | Path to the Graphviz `dot` executable. Required for Graphviz diagrams. |

**Windows example** (if not on PATH):
```
PDFLATEX_PATH=C:\texlive\2024\bin\windows\pdflatex.exe
DOT_PATH=C:\Program Files\Graphviz\bin\dot.exe
```

### Agent behaviour

| Variable | Default | Description |
|---|---|---|
| `MAX_AGENT_TURNS` | `20` | Maximum Claude API round-trips per request. Each render + inspection costs ~2 turns. |
| `MAX_REPAIR_ATTEMPTS` | `3` | How many times the agent tries to fix a broken diagram before giving up. |
| `VISUAL_SCORE_THRESHOLD` | `7.0` | Minimum visual validation score (0–10) to accept a render without repair. |

### Timeouts

| Variable | Default | Description |
|---|---|---|
| `RENDER_TIMEOUT` | `60` | Seconds before a pdflatex or Graphviz subprocess is killed. |
| `SANDBOX_TIMEOUT` | `30` | Seconds before the sandboxed Matplotlib subprocess is killed. |

---

## Architecture

### Workflow

```
User Prompt
     │
     ▼
┌─────────────┐
│  Classifier  │  → diagram type + complexity score
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Planner   │  → backend choice + structural spec (JSON)
└──────┬──────┘
       │
       ▼
┌──────────────┐
│ Code Generator│  → TikZ / Python / DOT source
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌─────────────────┐
│   Renderer   │────▶│  Error Handler  │
└──────┬───────┘     │ (syntax errors, │
       │              │  missing pkgs)  │
       │              └────────┬────────┘
       │                       │ retry with patch
       ▼                       ▼
┌──────────────┐     ┌─────────────────┐
│  Validator   │────▶│  Repair Agent   │──▶ back to Code Gen
└──────┬───────┘     └─────────────────┘
       │  pass
       ▼
  Final Output (PNG)
```

### Backend selection

| Diagram type | Best backend | Fallback |
|---|---|---|
| Geometric figures, proofs | TikZ | Matplotlib |
| Function plots, data visualization | Matplotlib | TikZ (pgfplots) |
| Trees, DAGs, automata, graphs | Graphviz | TikZ |
| Commutative diagrams | TikZ (`tikz-cd`) | — |
| Statistical / probability | Matplotlib | — |
| Circuit diagrams | TikZ (`circuitikz`) | — |

### Verification (two stages)

**Stage 1 — Compile-time** (fast, cheap): syntax check before rendering.
- TikZ: `pdflatex -draftmode`
- Matplotlib: `ast.parse()`
- Graphviz: `dot -Tsvg`

**Stage 2 — Visual** (expensive, accurate): the rendered PNG is shown to Claude, which checks labels, directions, geometric relationships, and mathematical notation, returning a score (0–10) and an issue list. Score < `VISUAL_SCORE_THRESHOLD` triggers a repair.

### File structure

```
├── agent.py                    # CLI entry point + agentic loop
├── config.py                   # all settings (reads from env)
├── .env.example                # documented env var template
│
├── backends/
│   ├── base.py                 # RenderResult dataclass
│   ├── tikz.py                 # pdflatex → pdf2image → PNG
│   ├── matplotlib_backend.py   # sanitize → sandboxed subprocess → PNG
│   └── graphviz_backend.py     # dot/neato/circo/fdp → PNG
│
├── sandbox/
│   └── matplotlib_runner.py    # isolated exec target (Agg backend forced)
│
├── validators/
│   ├── syntax.py               # pre-render static checks
│   └── visual.py               # VLM structured score + issues list
│
├── tools/
│   ├── registry.py             # Anthropic tool_use JSON schemas
│   └── implementations.py      # Python implementations; holds last-render state
│
├── prompts/
│   ├── system.md               # agent system prompt
│   ├── classify.md             # diagram classifier prompt
│   └── validate.md             # VLM visual validator prompt
│
└── output/                     # rendered diagrams saved here (git-ignored)
```

### Key design decisions

**The agent IS the validator.** Rendered images are returned as base64 image blocks inside the tool result, so Claude sees the diagram directly in the conversation and can assess it without a separate API call. `validate_visual` is an optional tool for when structured scoring is needed.

**Sandboxed Matplotlib.** Generated Python runs in a subprocess with the `Agg` backend forced, `plt.show()` stripped, and a hard timeout. It cannot write outside the temp directory.

**Stateless tools, stateful loop.** Each tool is a pure function (input → output). `_last_render` in `tools/implementations.py` is the only shared state — it lets `save_diagram` and `validate_visual` reference the most recent image without the agent passing raw bytes.
