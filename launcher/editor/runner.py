import runpy, sys
from pathlib import Path

def run_editor(project: Path, entry: str = "main.py") -> None:
    root=project.resolve(); script=(root / entry).resolve()
    if root not in script.parents or not script.is_file(): raise ValueError("Configured editor entry is missing or outside the repository")
    old_cwd, old_path = Path.cwd(), list(sys.path)
    try:
        import os; os.chdir(root); sys.path.insert(0, str(root)); runpy.run_path(str(script), run_name="__main__")
    finally:
        os.chdir(old_cwd); sys.path[:]=old_path
