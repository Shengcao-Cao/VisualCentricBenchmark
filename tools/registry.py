TOOL_DEFINITIONS = [
    {
        "name": "classify_diagram",
        "description": (
            "Classify the diagram type and receive a backend recommendation. "
            "Call this first to decide between TikZ, Matplotlib, and Graphviz."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "The diagram description to classify.",
                }
            },
            "required": ["description"],
        },
    },
    {
        "name": "render_tikz",
        "description": (
            "Compile and render a TikZ diagram. "
            "You may supply just the tikzpicture block or a full LaTeX document. "
            "The backend adds \\documentclass{standalone} and common packages automatically. "
            "Returns the rendered PNG image."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "TikZ / LaTeX source code.",
                }
            },
            "required": ["source"],
        },
    },
    {
        "name": "render_matplotlib",
        "description": (
            "Execute a Python / Matplotlib script and return the rendered diagram as a PNG. "
            "Do NOT call plt.show(); the backend saves the figure automatically. "
            "The script runs in a subprocess with the Agg (non-interactive) backend."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Python source code that produces a matplotlib figure.",
                }
            },
            "required": ["source"],
        },
    },
    {
        "name": "render_graphviz",
        "description": (
            "Render a Graphviz DOT language diagram. "
            "Provide complete DOT source including the graph/digraph wrapper. "
            "Returns the rendered PNG image."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "DOT language source code.",
                },
                "engine": {
                    "type": "string",
                    "description": (
                        "Layout engine. "
                        "dot=hierarchical (default), neato=spring, "
                        "circo=circular, fdp=force-directed, "
                        "sfdp=large-graph force-directed, twopi=radial."
                    ),
                    "enum": ["dot", "neato", "circo", "fdp", "sfdp", "twopi"],
                },
            },
            "required": ["source"],
        },
    },
    {
        "name": "validate_visual",
        "description": (
            "Ask a second Claude instance to score the last rendered diagram "
            "against the original description. Returns a JSON object with "
            "score (0–10), issues[], and suggestions[]. "
            "A score ≥ 7 is considered passing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "The original diagram description (used as reference).",
                }
            },
            "required": ["description"],
        },
    },
    {
        "name": "save_diagram",
        "description": "Save the most recently rendered diagram to the output/ directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Output filename, e.g. 'pythagorean_theorem.png'.",
                }
            },
            "required": ["filename"],
        },
    },
]
