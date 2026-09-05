from launcher.projects.manager import ProjectManager
from launcher.projects.model import Project
def test_atomic_project_roundtrip(tmp_path):
    manager=ProjectManager(tmp_path/"projects.json"); manager.add(Project("A",str(tmp_path/"a"),"https://github.com/a/a")); assert manager.load()[0].display_name=="A"
