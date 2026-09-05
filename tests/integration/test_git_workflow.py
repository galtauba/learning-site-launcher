import subprocess
from pathlib import Path
from launcher.git.repository import Repository
from launcher.git.sync import SyncService

def git(path: Path, *args: str): return subprocess.run(["git",*args],cwd=path,check=True,capture_output=True,text=True)
def test_commit_and_push_to_bare_origin(tmp_path):
    remote=tmp_path/"origin.git"; subprocess.run(["git","init","--bare",str(remote)],check=True,capture_output=True)
    project=tmp_path/"project"; project.mkdir(); git(project,"init"); git(project,"config","user.email","test@example.com"); git(project,"config","user.name","Test"); (project/"main.py").write_text("pass\n"); (project/"public").mkdir(); (project/"public"/"index.html").write_text("ok"); (project/"public"/"content").mkdir(); git(project,"add","."); git(project,"commit","-m","initial"); git(project,"branch","-M","main"); git(project,"remote","add","origin",str(remote)); git(project,"push","-u","origin","main")
    (project/"public"/"content"/"lesson.md").write_text("lesson")
    service=SyncService(Repository(project)); assert service.recover_dirty(); assert service.sync_origin()=="pushed local commits"
    assert "recovery autosave" in git(project,"log","--oneline","-1").stdout
