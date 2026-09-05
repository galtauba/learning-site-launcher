from dataclasses import dataclass
import subprocess
from pathlib import Path
from ..logging.sanitizer import sanitize

class GitError(RuntimeError): pass
@dataclass(frozen=True)
class GitResult:
    args: tuple[str, ...]; stdout: str; stderr: str; returncode: int
    @property
    def ok(self) -> bool: return self.returncode == 0

class GitClient:
    def __init__(self, executable: str = "git", timeout: int = 120): self.executable, self.timeout = executable, timeout
    def run(self, args: list[str], cwd: Path | None = None, check: bool = True, timeout: int | None = None) -> GitResult:
        command = [self.executable, *args]
        try: completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout or self.timeout)
        except FileNotFoundError as exc: raise GitError("Git for Windows was not found. Install Git and try again.") from exc
        except subprocess.TimeoutExpired as exc: raise GitError(f"Git operation timed out: {sanitize(' '.join(command))}") from exc
        result = GitResult(tuple(command), completed.stdout, completed.stderr, completed.returncode)
        if check and not result.ok: raise GitError(sanitize(result.stderr.strip() or result.stdout.strip() or "Git command failed"))
        return result
    def available(self) -> str | None:
        result = self.run(["--version"], check=False, timeout=10)
        return result.stdout.strip() if result.ok else None
