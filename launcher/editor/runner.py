import runpy, sys
import subprocess
from dataclasses import dataclass
from pathlib import Path

def run_editor(project: Path, entry: str = "main.py") -> None:
    root=project.resolve(); script=(root / entry).resolve()
    if root not in script.parents or not script.is_file(): raise ValueError("Configured editor entry is missing or outside the repository")
    old_cwd, old_path = Path.cwd(), list(sys.path)
    try:
        import os; os.chdir(root); sys.path.insert(0, str(root)); runpy.run_path(str(script), run_name="__main__")
    finally:
        os.chdir(old_cwd); sys.path[:]=old_path


@dataclass(frozen=True)
class EditorProcessResult:
    exit_code: int
    stdout: str
    stderr: str


def launch_editor_process(project: Path, entry: str = "main.py") -> EditorProcessResult:
    """Run the external editor in a separate process and wait for it to close.

    A Learning Site editor owns its own QApplication.  Running it inside the
    launcher's QApplication causes Qt's singleton error, so this deliberately
    invokes the packaged launcher again in ``--run-editor`` mode.  In source
    development it executes this package's entry-point file directly.  The
    editor's working directory is the user project, where ``python -m
    launcher`` would otherwise be unable to resolve the launcher package.
    """
    root = project.resolve()
    script = (root / entry).resolve()
    if root not in script.parents or not script.is_file():
        raise ValueError("Configured editor entry is missing or outside the repository")
    if getattr(sys, "frozen", False):
        command = [sys.executable, "--run-editor", str(root), "--entry", entry]
    else:
        entry_point = Path(__file__).resolve().parents[1] / "__main__.py"
        command = [sys.executable, str(entry_point), "--run-editor", str(root), "--entry", entry]
    completed = subprocess.run(command, cwd=root, check=False, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return EditorProcessResult(completed.returncode, completed.stdout, completed.stderr)
