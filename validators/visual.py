import base64
import json
from dataclasses import dataclass, field
from pathlib import Path

from config import DEFAULT_MODEL
from llm_client import simple_completion

_VALIDATE_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "validate.md"


@dataclass
class ValidationResult:
    passed: bool
    score: float  # 0–10
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    raw_feedback: str = ""


def validate_visual(image_bytes: bytes, description: str) -> ValidationResult:
    system = _VALIDATE_PROMPT_PATH.read_text(encoding="utf-8")
    b64 = base64.standard_b64encode(image_bytes).decode()

    raw = simple_completion(
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            f"Original diagram request:\n{description}\n\n"
                            "Evaluate the rendered diagram above against the request."
                        ),
                    },
                ],
            }
        ],
        system=system,
        model=DEFAULT_MODEL,
        max_tokens=1024,
    )

    try:
        data = json.loads(raw)
        score = float(data.get("score", 0))
        return ValidationResult(
            passed=score >= 7.0,
            score=score,
            issues=data.get("issues", []),
            suggestions=data.get("suggestions", []),
            raw_feedback=raw,
        )
    except (json.JSONDecodeError, ValueError):
        return ValidationResult(
            passed=False,
            score=0.0,
            issues=[raw],
            raw_feedback=raw,
        )
