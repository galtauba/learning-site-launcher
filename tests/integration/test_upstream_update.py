import subprocess
from pathlib import Path

from launcher.git.repository import Repository
from launcher.git.sync import SyncService


def git(path: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=path, check=True, capture_output=True, text=True).stdout


def test_tagged_upstream_release_is_merged_and_pushed(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    git(source, "init")
    git(source, "config", "user.email", "test@example.com")
    git(source, "config", "user.name", "Test")
    (source / "main.py").write_text("print('one')\n", encoding="utf-8")
    git(source, "add", ".")
    git(source, "commit", "-m", "initial")
    git(source, "branch", "-M", "main")
    git(source, "tag", "v1.0.0")
    upstream = tmp_path / "upstream.git"
    subprocess.run(["git", "clone", "--bare", str(source), str(upstream)], check=True, capture_output=True)

    user_origin = tmp_path / "user-origin.git"
    subprocess.run(["git", "init", "--bare", str(user_origin)], check=True, capture_output=True)
    project = tmp_path / "project"
    subprocess.run(["git", "clone", str(upstream), str(project)], check=True, capture_output=True)
    git(project, "config", "user.email", "test@example.com")
    git(project, "config", "user.name", "Test")
    git(project, "remote", "rename", "origin", "upstream")
    git(project, "remote", "add", "origin", str(user_origin))
    git(project, "push", "-u", "origin", "main")

    git(source, "remote", "add", "origin", str(upstream))
    (source / "main.py").write_text("print('two')\n", encoding="utf-8")
    git(source, "commit", "-am", "release")
    git(source, "tag", "v1.0.1")
    git(source, "push", "origin", "main", "--tags")

    service = SyncService(Repository(project))
    current, available = service.upstream_update_available()
    assert current is not None and current.name == "v1.0.0"
    assert available is not None and available.name == "v1.0.1"
    installed, applied = service.update_to_latest_stable()

    assert installed == "v1.0.0"
    assert applied == "v1.0.1"
    assert "two" in (project / "main.py").read_text(encoding="utf-8")
    assert git(project, "ls-remote", "origin", "refs/heads/main")
