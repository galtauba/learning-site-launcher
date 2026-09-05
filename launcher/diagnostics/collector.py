import platform, shutil
from pathlib import Path
from ..git.repository import Repository
from ..git.client import GitClient, GitError
from ..version import __version__

def collect(project: Path | None = None) -> dict[str, str]:
    git=GitClient(); report={"launcherVersion":__version__, "windowsVersion":platform.platform(), "git":git.available() or "Unavailable", "gitCredentialManager":shutil.which("git-credential-manager") or "Unavailable"}
    if project:
        report["projectPath"]=str(project)
        try:
            repo=Repository(project); report.update({"branch":repo.branch(), "head":repo.run(["rev-parse","HEAD"]).stdout.strip(), "workingTree":"dirty" if repo.is_dirty() else "clean", "origin":repo.remote_url("origin")})
            try: report["upstream"]=repo.remote_url("upstream")
            except GitError: report["upstream"]="Not configured"
        except GitError as exc: report["repositoryError"]=str(exc)
    return report
