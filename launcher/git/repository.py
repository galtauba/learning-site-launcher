from pathlib import Path
from .client import GitClient, GitError

class Repository:
    def __init__(self, root: Path, git: GitClient | None = None): self.root, self.git = root.resolve(), git or GitClient()
    def run(self, args: list[str], **kw): return self.git.run(args, self.root, **kw)
    def branch(self) -> str:
        value = self.run(["symbolic-ref", "--quiet", "--short", "HEAD"], check=False)
        if not value.ok: raise GitError("Detached HEAD: repair the branch before making changes.")
        return value.stdout.strip()
    def remote_url(self, name: str) -> str: return self.run(["remote", "get-url", name]).stdout.strip()
    def status(self) -> list[tuple[str, str]]:
        return [(line[:2], line[3:]) for line in self.run(["status", "--porcelain=v1"]).stdout.splitlines()]
    def is_dirty(self) -> bool: return bool(self.status())
    def ahead_behind(self, remote_ref: str) -> tuple[int, int]:
        branch = self.branch(); output = self.run(["rev-list", "--left-right", "--count", f"{branch}...{remote_ref}"]).stdout.split()
        return int(output[0]), int(output[1])
    def checkpoint(self, label: str) -> str:
        branch = self.branch(); stamp = self.run(["rev-parse", "--short", "HEAD"]).stdout.strip()
        name = f"launcher/checkpoint/{label}-{stamp}"
        self.run(["branch", name, branch]); return name
    def commit_all(self, message: str) -> bool:
        if not self.is_dirty(): return False
        self.run(["add", "-A"]); self.run(["commit", "-m", message]); return True
