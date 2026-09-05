from pathlib import Path
from .constants import app_data_dir

def ensure_data_directories() -> Path:
    root = app_data_dir()
    for name in ("state", "logs", "backups", "downloads", "locks"):
        (root / name).mkdir(parents=True, exist_ok=True)
    return root
