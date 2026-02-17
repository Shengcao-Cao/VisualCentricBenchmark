#!/usr/bin/env python
"""Sandboxed matplotlib execution runner.

Usage:
    python matplotlib_runner.py <script_path>

The generated script is executed in a clean namespace with the Agg backend
forced. The DIAGRAM_OUTPUT_PATH environment variable controls where the
figure is saved.
"""
import sys


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: matplotlib_runner.py <script_path>", file=sys.stderr)
        sys.exit(1)

    script_path = sys.argv[1]

    try:
        with open(script_path, encoding="utf-8") as fh:
            source = fh.read()
    except OSError as exc:
        print(f"Cannot read script: {exc}", file=sys.stderr)
        sys.exit(1)

    code = compile(source, script_path, "exec")

    namespace: dict = {"__name__": "__main__", "__file__": script_path}
    try:
        exec(code, namespace)  # noqa: S102
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
