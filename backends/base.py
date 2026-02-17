from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RenderResult:
    success: bool
    image_bytes: bytes | None = None
    format: str = "png"
    stdout: str = ""
    stderr: str = ""
    error: str = ""
    backend: str = ""
    source_code: str = ""
    output_path: Path | None = None
