"""Load and validate Person A's permission knowledge-base JSON."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any


def load_knowledge_base(path: str | Path = "data/permissions.json") -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(
            f"Permission knowledge base not found at {file_path}. "
            "Place Person A's permissions.json at this path or pass its path explicitly."
        )
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {file_path}: {exc}") from exc
    if not isinstance(data, (dict, list)):
        raise ValueError("Permission knowledge base must be a JSON object or list.")
    if isinstance(data, list):
        return {"permissions": data}
    return data
