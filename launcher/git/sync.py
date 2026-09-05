from datetime import datetime
from .repository import Repository
from .client import GitError
from .versions import StableTag, stable_tags

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

    def stable_upstream_tags(self) -> list[StableTag]:
        """Fetch and return stable semantic version tags published by upstream."""
        has_upstream = self.repo.run(["remote", "get-url", "upstream"], check=False)
        if not has_upstream.ok:
            return []
        self.repo.run(["fetch", "upstream", "--tags", "--prune"], timeout=900)
        output = self.repo.run(["ls-remote", "--tags", "upstream"], timeout=120).stdout
        names: set[str] = set()
        for line in output.splitlines():
            pieces = line.split("\t", 1)
            if len(pieces) != 2 or not pieces[1].startswith("refs/tags/"):
                continue
            names.add(pieces[1].removeprefix("refs/tags/").removesuffix("^{}"))
        return stable_tags(list(names))

    def latest_stable_upstream_tag(self) -> StableTag | None:
        tags = self.stable_upstream_tags()
        return tags[0] if tags else None

    def installed_stable_tag(self, candidates: list[StableTag]) -> StableTag | None:
        """Find the newest upstream stable tag already contained in HEAD."""
        for candidate in candidates:
            contained = self.repo.run(
                ["merge-base", "--is-ancestor", candidate.name, "HEAD"], check=False
            )
            if contained.ok:
                return candidate
        return None

    def update_to_latest_stable(self) -> tuple[str | None, str | None]:
        """Apply one newer official stable release, preserving user Git history.

        Returns ``(installed_tag, applied_tag)``.  A merge conflict deliberately
        raises ``GitError`` and is left intact for the user to resolve; it is
        never discarded or force-pushed.
        """
        available = self.stable_upstream_tags()
        if not available:
            return None, None
        latest = available[0]
        installed = self.installed_stable_tag(available)
        if installed is not None and installed.version >= latest.version:
            return installed.name, None
        self.repo.checkpoint("pre-upstream-update")
        self.repo.run(["merge", "--no-edit", latest.name])
        self.repo.run(["push", "origin", self.repo.branch()], timeout=900)
        return installed.name if installed else None, latest.name

    def upstream_update_available(self) -> tuple[StableTag | None, StableTag | None]:
        """Return installed/latest tags only when an official update is newer."""
        available = self.stable_upstream_tags()
        if not available:
            return None, None
        installed, latest = self.installed_stable_tag(available), available[0]
        if installed is None or latest.version > installed.version:
            return installed, latest
        return installed, None
