from datetime import datetime, timezone
from pathlib import Path
from ..git.repository import Repository

def create_checkpoint(project: Path, label: str) -> str:
    """Create a recoverable local Git branch; never alters working files."""
    safe_label = "".join(ch for ch in label.lower() if ch.isalnum() or ch in "-_") or "manual"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return Repository(project).checkpoint(f"{safe_label}-{stamp}")
