from launcher.projects.manager import ProjectManager
from launcher.projects.model import Project


def test_delete_local_clone_removes_only_registered_git_directory(tmp_path):
    project = tmp_path / "site"
    project.mkdir()
    (project / ".git").mkdir()
    (project / "content.txt").write_text("local content", encoding="utf-8")
    unrelated = tmp_path / "unrelated.txt"
    unrelated.write_text("keep", encoding="utf-8")
    manager = ProjectManager(tmp_path / "projects.json")
    manager.add(Project("Site", str(project), "https://github.com/example/site"))

    manager.delete_local_clone(project)

    assert not project.exists()
    assert unrelated.exists()
    assert manager.load() == []
