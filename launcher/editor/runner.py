import runpy, sys
import subprocess
from pathlib import Path

def run_editor(project: Path, entry: str = "main.py") -> None:
    root=project.resolve(); script=(root / entry).resolve()
    if root not in script.parents or not script.is_file(): raise ValueError("Configured editor entry is missing or outside the repository")
    old_cwd, old_path = Path.cwd(), list(sys.path)
    try:
        import os; os.chdir(root); sys.path.insert(0, str(root)); runpy.run_path(str(script), run_name="__main__")
    finally:
        os.chdir(old_cwd); sys.path[:]=old_path


def launch_editor_process(project: Path, entry: str = "main.py") -> int:
    """Run the external editor in a separate process and wait for it to close.

    A Learning Site editor owns its own QApplication.  Running it inside the
    launcher's QApplication causes Qt's singleton error, so this deliberately
    invokes the packaged launcher again in ``--run-editor`` mode.  In source
    development it uses ``python -m launcher`` instead.
    """
    root = project.resolve()
    script = (root / entry).resolve()
    if root not in script.parents or not script.is_file():
        raise ValueError("Configured editor entry is missing or outside the repository")
    if getattr(sys, "frozen", False):
        command = [sys.executable, "--run-editor", str(root), "--entry", entry]
    else:
        command = [sys.executable, "-m", "launcher", "--run-editor", str(root), "--entry", entry]
    completed = subprocess.run(command, cwd=root, check=False)
    return completed.returncode
