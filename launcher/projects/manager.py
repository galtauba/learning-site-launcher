import json, os, shutil, stat, tempfile
from pathlib import Path
from .model import Project
from ..paths import ensure_data_directories

class ProjectManager:
    """Atomic, schema-versioned local project registry."""
    schema_version = 1
    def __init__(self, path: Path | None = None): self.path = path or ensure_data_directories() / "projects.json"
    def load(self) -> list[Project]:
        if not self.path.exists(): return []
        try: data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError): return []
        return [Project.from_dict(p) for p in data.get("projects", []) if isinstance(p, dict)]
    def save(self, projects: list[Project]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(dir=self.path.parent, prefix="projects-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump({"schemaVersion": self.schema_version, "projects": [p.to_dict() for p in projects]}, fh, indent=2)
                fh.flush(); os.fsync(fh.fileno())
            os.replace(temp, self.path)
        finally:
            if os.path.exists(temp): os.unlink(temp)
    def add(self, project: Project) -> None:
        projects = self.load()
        if any(Path(p.local_path) == Path(project.local_path) for p in projects): raise ValueError("This local project is already registered")
        projects.append(project); self.save(projects)
    def remove(self, path: Path) -> None: self.save([p for p in self.load() if Path(p.local_path) != path])
    def update(self, project: Project) -> None:
        projects = self.load()
        for index, existing in enumerate(projects):
            if Path(existing.local_path) == Path(project.local_path):
                projects[index] = project
                self.save(projects)
                return
        raise ValueError("Cannot update a project that is not registered")

    def delete_local_clone(self, path: Path) -> None:
        """Delete one validated local project directory and unregister it.

        This never contacts a remote.  Basic boundary checks prevent an
        accidental attempt to remove a drive root or a non-project directory.
        """
        root = path.resolve()
        if not root.is_dir() or root == Path(root.anchor):
            raise ValueError("The selected local project directory is not safe to delete")
        if not (root / ".git").exists():
            raise ValueError("Refusing to delete a directory that is not a Git project")

        def clear_readonly(func, target, _exc):
            os.chmod(target, stat.S_IWRITE)
            func(target)

        shutil.rmtree(root, onerror=clear_readonly)
        self.remove(root)
