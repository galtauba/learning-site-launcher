from pathlib import Path
from .client import GitClient, GitError
from .repository import Repository
from ..constants import OFFICIAL_LEARNING_SITE_GIT_URL

def clone(url: str, destination: Path, git: GitClient | None = None) -> Path:
    if destination.exists() and any(destination.iterdir()): raise ValueError("Clone destination is not empty")
    destination.parent.mkdir(parents=True, exist_ok=True); (git or GitClient()).run(["clone", url, str(destination)], cwd=destination.parent, timeout=900)
    return destination


def repository_is_empty(root: Path, git: GitClient | None = None) -> bool:
    """Return whether a cloned repository has no commits yet."""
    client = git or GitClient()
    return not client.run(["rev-parse", "--verify", "HEAD"], cwd=root, check=False).ok


def initialize_empty_repository_from_official(root: Path) -> str:
    """Seed an empty user origin from the official repository without rewriting history.

    The resulting branch starts at upstream's branch tip, so all future tagged
    upstream updates share Git ancestry and can be safely merged.  The user's
    origin remains the only remote ever pushed to by the launcher.
    """
    repo = Repository(root)
    if not repository_is_empty(root, repo.git):
        raise ValueError("Initial setup is available only for an empty repository")
    existing = repo.run(["remote", "get-url", "upstream"], check=False)
    if existing.ok and existing.stdout.strip() != OFFICIAL_LEARNING_SITE_GIT_URL:
        raise GitError("An existing upstream remote points to a different repository")
    if not existing.ok:
        repo.run(["remote", "add", "upstream", OFFICIAL_LEARNING_SITE_GIT_URL])
    repo.run(["fetch", "upstream", "--tags", "--prune"], timeout=900)
    head = repo.run(["ls-remote", "--symref", "upstream", "HEAD"], timeout=120).stdout
    branch = next((line.split("refs/heads/", 1)[1].split("\t", 1)[0]
                   for line in head.splitlines() if line.startswith("ref: refs/heads/")), "main")
    remote_branch = repo.run(["show-ref", "--verify", f"refs/remotes/upstream/{branch}"], check=False)
    if not remote_branch.ok:
        raise GitError("The official Learning Site default branch could not be found")
    repo.run(["checkout", "-B", branch, f"upstream/{branch}"])
    repo.run(["push", "-u", "origin", branch], timeout=900)
    return branch
