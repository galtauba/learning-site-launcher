import json
from pathlib import Path
from ..constants import DEFAULT_METADATA

def load_metadata(root: Path) -> dict:
    path = root / ".learning-site.json"
    if not path.is_file(): return dict(DEFAULT_METADATA)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid .learning-site.json: {exc}") from exc
    if not isinstance(value, dict): raise ValueError(".learning-site.json must be a JSON object")
    return {**DEFAULT_METADATA, **value}
