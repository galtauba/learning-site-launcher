from pathlib import Path
from .client import GitClient

def clone(url: str, destination: Path, git: GitClient | None = None) -> Path:
    if destination.exists() and any(destination.iterdir()): raise ValueError("Clone destination is not empty")
    destination.parent.mkdir(parents=True, exist_ok=True); (git or GitClient()).run(["clone", url, str(destination)], cwd=destination.parent, timeout=900)
    return destination
