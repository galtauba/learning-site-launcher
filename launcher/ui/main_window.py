from pathlib import Path
from PySide6.QtCore import Qt, QThreadPool, QRunnable, Signal, QObject
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QMessageBox, QInputDialog, QFileDialog
from ..constants import APP_NAME, GIT_DOWNLOAD_URL, default_projects_dir
from ..git.client import GitClient, GitError
from ..git.clone import clone
from ..git.repository import Repository
from ..git.sync import SyncService
from ..github.client import GitHubClient
from ..projects.manager import ProjectManager
from ..projects.model import Project, ProjectState
from ..projects.validator import validate_learning_site
from ..projects.metadata import load_metadata
from ..editor.runner import run_editor

class WorkerSignals(QObject):
    done=Signal(object); failed=Signal(str)
class Worker(QRunnable):
    def __init__(self, action): super().__init__(); self.action=action; self.signals=WorkerSignals()
    def run(self):
        try: self.signals.done.emit(self.action())
        except Exception as exc: self.signals.failed.emit(str(exc))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.manager=ProjectManager(); self.pool=QThreadPool.globalInstance(); self.setWindowTitle(APP_NAME); self.resize(780,520)
        central=QWidget(); layout=QVBoxLayout(central); title=QLabel("Learning Site Launcher\nMy Sites"); title.setStyleSheet("font-size: 24px; font-weight: 600; padding: 12px;"); layout.addWidget(title)
        self.sites=QListWidget(); self.sites.itemSelectionChanged.connect(self._selection); layout.addWidget(self.sites)
        actions=QHBoxLayout(); self.add=QPushButton("+ Add Site"); self.existing=QPushButton("Add Existing Local Project"); self.open=QPushButton("Open Editor"); self.sync=QPushButton("Sync"); self.history=QPushButton("History");
        for button in (self.add,self.existing,self.open,self.sync,self.history): actions.addWidget(button)
        layout.addLayout(actions); self.setCentralWidget(central); self.add.clicked.connect(self.add_site); self.existing.clicked.connect(self.add_existing); self.open.clicked.connect(self.open_editor); self.sync.clicked.connect(self.sync_project); self.history.clicked.connect(self.show_history); self.refresh()
        if not GitClient().available(): self.show_prerequisite()
    def selected(self) -> Project | None:
        row=self.sites.currentRow(); projects=self.manager.load(); return projects[row] if 0<=row<len(projects) else None
    def _selection(self):
        enabled=self.selected() is not None
        for button in (self.open,self.sync,self.history): button.setEnabled(enabled)
    def refresh(self):
        self.sites.clear()
        for p in self.manager.load(): self.sites.addItem(f"{p.display_name}\n{p.origin_url}\nLocal: {p.state}   Learning Site: {p.current_version}")
        self._selection()
    def show_prerequisite(self):
        message=QMessageBox(self); message.setWindowTitle("Git for Windows required"); message.setText("Git for Windows is required to use Learning Site Launcher."); download=message.addButton("Download Git for Windows", QMessageBox.ActionRole); again=message.addButton("Check Again", QMessageBox.AcceptRole); message.addButton("Exit", QMessageBox.RejectRole); message.exec()
        if message.clickedButton() is download:
            import webbrowser; webbrowser.open(GIT_DOWNLOAD_URL)
        elif message.clickedButton() is again and not GitClient().available(): self.show_prerequisite()
        elif message.clickedButton() is not again: self.close()
    def start(self, action, success):
        worker=Worker(action); worker.signals.done.connect(lambda value:(success(value),self.refresh())); worker.signals.failed.connect(lambda error:QMessageBox.critical(self,APP_NAME,error)); self.pool.start(worker)
    def add_site(self):
        url,ok=QInputDialog.getText(self,"Add Site","Paste your GitHub fork URL:")
        if not(ok and url.strip()): return
        name,ok=QInputDialog.getText(self,"Add Site","Display name:",text=Path(url.rstrip("/")).stem)
        if not ok:return
        destination=default_projects_dir()/name
        def action():
            root=clone(url.strip(),destination); repo=Repository(root); branch=repo.branch(); gh=GitHubClient(); upstream=gh.root_clone_url(url.strip()) or ""; valid=validate_learning_site(root)
            if not valid.valid: raise ValueError("Not a Learning Site project. Missing: "+", ".join(valid.missing))
            if upstream and upstream != repo.remote_url("origin"):
                existing=repo.run(["remote","get-url","upstream"],check=False)
                if not existing.ok: repo.run(["remote","add","upstream",upstream])
            metadata=load_metadata(root); trusted=upstream.endswith("galtauba/LearningSite.git")
            self.manager.add(Project(name,str(root),repo.remote_url("origin"),upstream,branch,metadata.get("siteVersion","Unversioned / Legacy"),trusted=trusted,state=ProjectState.READY.value))
        self.start(action,lambda _:None)
    def add_existing(self):
        path=QFileDialog.getExistingDirectory(self,"Choose Learning Site repository")
        if not path:return
        def action():
            root=Path(path); valid=validate_learning_site(root)
            if not valid.valid: raise ValueError("Not a Learning Site project. Missing: "+", ".join(valid.missing))
            repo=Repository(root)
            # Imported repositories are deliberately untrusted until the UI confirms it.
            self.manager.add(Project(root.name,str(root),repo.remote_url("origin"),branch=repo.branch(),trusted=False,state=ProjectState.READY.value))
        self.start(action,lambda _:None)
    def open_editor(self):
        p=self.selected()
        if not p:return
        if not p.trusted:
            QMessageBox.warning(self,APP_NAME,"This repository is not trusted. Its Python editor will not be executed."); return
        def action():
            metadata=load_metadata(p.path()); run_editor(p.path(),metadata["editorEntry"]); repo=Repository(p.path()); SyncService(repo).recover_dirty();
            if p.auto_push: SyncService(repo).sync_origin()
        self.start(action,lambda _:None)
    def sync_project(self):
        p=self.selected()
        if p:self.start(lambda:SyncService(Repository(p.path())).sync_origin(),lambda _:None)
    def show_history(self):
        p=self.selected()
        if not p:return
        try: text=Repository(p.path()).run(["log","--oneline","-20"]).stdout
        except GitError as exc:text=str(exc)
        QMessageBox.information(self,"History",text or "No commits found.")
