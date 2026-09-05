"""Safe recognition of repositories derived from the official Learning Site."""
from .repository import Repository
from ..constants import OFFICIAL_LEARNING_SITE_GIT_URL


def _normalize_remote(url: str) -> str:
    return url.strip().rstrip("/").removesuffix(".git")


def configure_official_upstream_if_related(repo: Repository) -> bool:
    """Configure official upstream only when the repository shares Git history.

    A remote URL alone is not proof that a repository is safe to execute.  This
    function fetches the official source and requires a common Git ancestor. If
    it added an upstream remote but cannot prove the relationship, it removes
    that temporary remote again.
    """
    current = repo.run(["remote", "get-url", "upstream"], check=False)
    added_here = False
    if current.ok:
        if _normalize_remote(current.stdout) != _normalize_remote(OFFICIAL_LEARNING_SITE_GIT_URL):
            return False
    else:
        repo.run(["remote", "add", "upstream", OFFICIAL_LEARNING_SITE_GIT_URL])
        added_here = True
    try:
        repo.run(["fetch", "upstream", "--tags", "--prune"], timeout=900)
        common = repo.run(["merge-base", "HEAD", "upstream/main"], check=False)
        return common.ok and bool(common.stdout.strip())
    finally:
        # Do not leave an unrelated repository appearing to be official.
        common = repo.run(["merge-base", "HEAD", "upstream/main"], check=False)
        if added_here and not (common.ok and common.stdout.strip()):
            repo.run(["remote", "remove", "upstream"], check=False)
