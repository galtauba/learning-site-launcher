from datetime import datetime
from .repository import Repository
from .client import GitError

def timestamp_message(prefix: str) -> str:
    """Build a user-facing commit message using the computer's local clock."""
    return f"Learning Site: {prefix} - {datetime.now().astimezone():%Y-%m-%d %H:%M}"

class SyncService:
    def __init__(self, repo: Repository): self.repo=repo
    def recover_dirty(self) -> bool:
        if not self.repo.is_dirty(): return False
        self.repo.checkpoint("pre-recovery"); return self.repo.commit_all(timestamp_message("recovery autosave"))
    def sync_origin(self) -> str:
        branch=self.repo.branch(); self.repo.run(["fetch", "origin", "--prune"]); ahead, behind=self.repo.ahead_behind(f"origin/{branch}")
        if ahead and behind:
            self.repo.checkpoint("pre-origin-merge"); self.repo.run(["merge", "--no-edit", f"origin/{branch}"]); self.repo.run(["push", "origin", branch]); return "merged diverged origin"
        if behind:
            self.repo.checkpoint("pre-origin-merge"); self.repo.run(["merge", "--no-edit", f"origin/{branch}"]); return "merged origin"
        if ahead:
            self.repo.run(["push", "origin", branch]); return "pushed local commits"
        return "synced"
    def apply_tag(self, tag: str) -> None:
        self.repo.run(["fetch", "upstream", "--tags", "--prune"]); self.repo.checkpoint("pre-upstream-update")
        self.repo.run(["merge", "--no-edit", tag]); self.repo.run(["push", "origin", self.repo.branch()])
    def abort_merge(self) -> None: self.repo.run(["merge", "--abort"])
