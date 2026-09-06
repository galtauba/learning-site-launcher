from pathlib import Path
from PySide6.QtCore import Qt, QThreadPool, QRunnable, Signal, QObject
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QMessageBox, QInputDialog, QFileDialog, QProgressDialog, QDialog, QCheckBox, QDialogButtonBox
from ..constants import APP_NAME, GIT_DOWNLOAD_URL, OFFICIAL_LEARNING_SITE_GIT_URL, default_projects_dir
from ..git.client import GitClient, GitError
from ..git.clone import clone, repository_is_empty, initialize_empty_repository_from_official
from ..git.repository import Repository
from ..git.sync import SyncService
from ..git.upstream import configure_official_upstream_if_related
from ..github.client import GitHubClient
from ..projects.manager import ProjectManager
from ..projects.model import Project, ProjectState
from ..projects.validator import validate_learning_site
from ..projects.metadata import load_metadata
from ..editor.runner import launch_editor_process

class WorkerSignals(QObject):
    done=Signal(object); failed=Signal(str)
class Worker(QRunnable):
    def __init__(self, action): super().__init__(); self.action=action; self.signals=WorkerSignals()
    def run(self):
        try: self.signals.done.emit(self.action())
        except Exception as exc: self.signals.failed.emit(str(exc))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.manager=ProjectManager(); self.pool=QThreadPool.globalInstance(); self._active_workers: set[Worker] = set(); self.setWindowTitle(APP_NAME); self.resize(780,520)
        central=QWidget(); layout=QVBoxLayout(central); title=QLabel("Learning Site Launcher\nMy Sites"); title.setStyleSheet("font-size: 24px; font-weight: 600; padding: 12px;"); layout.addWidget(title)
        self.sites=QListWidget(); self.sites.itemSelectionChanged.connect(self._selection); layout.addWidget(self.sites)
        actions=QHBoxLayout(); self.add=QPushButton("+ Add Site"); self.existing=QPushButton("Add Existing Local Project"); self.open=QPushButton("Open Editor"); self.sync=QPushButton("Sync"); self.history=QPushButton("History"); self.identity=QPushButton("Git Identity"); self.settings=QPushButton("Project Settings"); self.delete=QPushButton("Delete Local Clone")
        self.delete.setToolTip("Delete only the local project folder. The GitHub repository is not affected.")
        self.identity.setToolTip("Set the Git author name and email for this site only.")
        for button in (self.add,self.existing,self.open,self.sync,self.history,self.identity,self.settings,self.delete): actions.addWidget(button)
        layout.addLayout(actions); self.setCentralWidget(central); self.add.clicked.connect(self.add_site); self.existing.clicked.connect(self.add_existing); self.open.clicked.connect(self.open_editor); self.sync.clicked.connect(self.sync_project); self.history.clicked.connect(self.show_history); self.identity.clicked.connect(self.configure_git_identity); self.settings.clicked.connect(self.configure_project_settings); self.delete.clicked.connect(self.delete_local_clone); self.refresh()
        if not GitClient().available(): self.show_prerequisite()
    def selected(self) -> Project | None:
        row=self.sites.currentRow(); projects=self.manager.load(); return projects[row] if 0<=row<len(projects) else None
    def _selection(self):
        busy = bool(self._active_workers)
        self.add.setEnabled(not busy)
        self.existing.setEnabled(not busy)
        enabled = self.selected() is not None and not busy
        for button in (self.open,self.sync,self.history,self.identity,self.settings,self.delete): button.setEnabled(enabled)
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
    def start(self, description: str, action, success=lambda _value: None):
        """Run slow work off the UI thread with an explicit busy indication.

        Git does not provide reliable percentage progress for every operation
        (notably merge and commit), so an indeterminate progress bar is both
        accurate and keeps the window responsive.  It is intentionally not
        cancellable: abruptly killing Git can leave a repository mid-merge.
        """
        progress = QProgressDialog(description, None, 0, 0, self)
        progress.setWindowTitle(APP_NAME)
        progress.setWindowModality(Qt.ApplicationModal)
        progress.setAutoClose(False)
        progress.setAutoReset(False)
        progress.setMinimumDuration(0)
        progress.setCancelButton(None)
        progress.show()
        for button in (self.add, self.existing, self.open, self.sync, self.history, self.identity, self.settings, self.delete):
            button.setEnabled(False)
        worker = Worker(action)

        def complete(value):
            progress.close()
            self._active_workers.discard(worker)
            success(value)
            self.refresh()

        def failed(error: str):
            progress.close()
            self._active_workers.discard(worker)
            self.refresh()
            QMessageBox.critical(self, APP_NAME, error)

        worker.signals.done.connect(complete)
        worker.signals.failed.connect(failed)
        # QThreadPool owns the native QRunnable, but retaining the Python
        # wrapper keeps its Qt signal object alive until the queued result is
        # delivered to the main thread.
        self._active_workers.add(worker)
        self.pool.start(worker)
    def add_site(self):
        url,ok=QInputDialog.getText(self,"Add Site","Paste your GitHub fork URL:")
        if not(ok and url.strip()): return
        name,ok=QInputDialog.getText(self,"Add Site","Display name:",text=Path(url.rstrip("/")).stem)
        if not ok:return
        destination=default_projects_dir()/name
        def action():
            requested_url = url.strip().rstrip("/").removesuffix(".git")
            if destination.is_dir() and (destination / ".git").exists():
                root = destination
                existing_url = Repository(root).remote_url("origin").rstrip("/").removesuffix(".git")
                if existing_url != requested_url:
                    raise ValueError("The chosen project folder already belongs to a different repository")
            else:
                root = clone(url.strip(), destination)
            if repository_is_empty(root):
                return {"empty": True, "root": root}
            repo=Repository(root); branch=repo.branch(); gh=GitHubClient(); upstream=gh.root_clone_url(url.strip()) or ""; valid=validate_learning_site(root)
            if not valid.valid: raise ValueError("Not a Learning Site project. Missing: "+", ".join(valid.missing))
            if upstream and upstream != repo.remote_url("origin"):
                existing=repo.run(["remote","get-url","upstream"],check=False)
                if not existing.ok: repo.run(["remote","add","upstream",upstream])
            trusted = upstream.endswith("galtauba/LearningSite.git")
            if not trusted and configure_official_upstream_if_related(repo):
                upstream = repo.remote_url("upstream")
                trusted = True
            metadata=load_metadata(root)
            self.manager.add(Project(name,str(root),repo.remote_url("origin"),upstream,branch,metadata.get("siteVersion","Unversioned / Legacy"),trusted=trusted,state=ProjectState.READY.value))
            return {"empty": False, "root": root}

        def after_clone(result):
            if not result["empty"]:
                return
            answer = QMessageBox.question(
                self,
                "Set up empty repository",
                "This repository is empty and is not a Learning Site fork.\n\n"
                "Set it up as a new Learning Site project? The official Learning Site "
                "will be copied into your repository now. Future official updates will "
                "be read from upstream and pushed only to your repository.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if answer != QMessageBox.Yes:
                return

            root = result["root"]
            def initial_setup():
                branch = initialize_empty_repository_from_official(root)
                valid = validate_learning_site(root)
                if not valid.valid:
                    raise ValueError("Official repository does not contain the required Learning Site files")
                metadata = load_metadata(root)
                repo = Repository(root)
                self.manager.add(Project(
                    name, str(root), repo.remote_url("origin"), repo.remote_url("upstream"), branch,
                    metadata.get("siteVersion", "Unversioned / Legacy"), trusted=True,
                    state=ProjectState.READY.value,
                ))
            self.start("Setting up your new Learning Site repository…", initial_setup)

        self.start("Cloning your repository and checking Learning Site…", action, after_clone)
    def add_existing(self):
        path=QFileDialog.getExistingDirectory(self,"Choose Learning Site repository")
        if not path:return
        def action():
            root=Path(path); valid=validate_learning_site(root)
            if not valid.valid: raise ValueError("Not a Learning Site project. Missing: "+", ".join(valid.missing))
            repo=Repository(root)
            origin = repo.remote_url("origin")
            configured_upstream = repo.run(["remote", "get-url", "upstream"], check=False)
            upstream = configured_upstream.stdout.strip() if configured_upstream.ok else ""
            normalize_remote = lambda value: value.rstrip("/").removesuffix(".git")
            official = normalize_remote(upstream) == normalize_remote(OFFICIAL_LEARNING_SITE_GIT_URL)
            if not official:
                discovered = GitHubClient().root_clone_url(origin)
                official = bool(discovered and normalize_remote(discovered) == normalize_remote(OFFICIAL_LEARNING_SITE_GIT_URL))
                if official and not upstream:
                    repo.run(["remote", "add", "upstream", OFFICIAL_LEARNING_SITE_GIT_URL])
                    upstream = OFFICIAL_LEARNING_SITE_GIT_URL
            if not official and configure_official_upstream_if_related(repo):
                upstream = repo.remote_url("upstream")
                official = True
            self.manager.add(Project(root.name, str(root), origin, upstream, repo.branch(), trusted=official, state=ProjectState.READY.value))
        self.start("Checking the local Learning Site repository…", action)
    def open_editor(self):
        p=self.selected()
        if not p:return
        if not p.trusted:
            def verify_official_lineage():
                repo = Repository(p.path())
                return configure_official_upstream_if_related(repo)

            def after_verification(verified):
                if not verified:
                    QMessageBox.warning(
                        self,
                        APP_NAME,
                        "This repository is not trusted. Its Python editor will not be executed.",
                    )
                    return
                p.trusted = True
                self.manager.update(p)
                self.open_editor()

            self.start("Verifying the official Learning Site project…", verify_official_lineage, after_verification)
            return
        def launch_after_check():
            def action():
                metadata=load_metadata(p.path())
                result = launch_editor_process(p.path(), metadata["editorEntry"])
                if result.exit_code != 0:
                    details = (result.stderr or result.stdout).strip()
                    suffix = f"\n\nDetails:\n{details[-1200:]}" if details else ""
                    raise RuntimeError(f"The Learning Site editor closed with exit code {result.exit_code}.{suffix}")
                repo=Repository(p.path()); SyncService(repo).recover_dirty()
                if p.auto_push: SyncService(repo).sync_origin()
            self.start("The editor is open. Saving and synchronizing changes when it closes…", action)

        def check_for_update():
            service = SyncService(Repository(p.path()))
            service.recover_dirty()
            service.sync_origin(push_local=p.auto_push)
            installed, latest = service.upstream_update_available() if p.auto_updates else (None, None)
            return installed.name if installed else None, latest.name if latest else None

        def after_check(result):
            installed, latest = result
            if not latest:
                launch_after_check()
                return
            answer = QMessageBox.question(
                self,
                "Learning Site update available",
                f"A new official Learning Site version is available: {latest}.\n"
                f"Current version: {installed or 'Unversioned / Legacy'}.\n\n"
                "Update now before opening the editor?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if answer != QMessageBox.Yes:
                launch_after_check()
                return

            def apply_update():
                return SyncService(Repository(p.path())).update_to_latest_stable()

            def after_update(update_result):
                _previous, applied = update_result
                if applied:
                    p.current_version = applied
                    p.last_applied_upstream_tag = applied
                    p.last_applied_upstream_commit = Repository(p.path()).run(["rev-parse", applied]).stdout.strip()
                    self.manager.update(p)
                launch_after_check()

            self.start(f"Updating Learning Site to {latest}…", apply_update, after_update)

        self.start("Checking for official Learning Site updates…", check_for_update, after_check)
    def sync_project(self):
        p=self.selected()
        if p:
            def synchronize():
                service = SyncService(Repository(p.path()))
                service.recover_dirty()
                origin_result = service.sync_origin()
                installed, applied = service.update_to_latest_stable() if p.auto_updates else (None, None)
                return origin_result, installed, applied

            def sync_complete(result):
                _origin_result, installed, applied = result
                if applied:
                    p.current_version = applied
                    p.last_applied_upstream_tag = applied
                    p.last_applied_upstream_commit = Repository(p.path()).run(["rev-parse", applied]).stdout.strip()
                    self.manager.update(p)
                    QMessageBox.information(
                        self,
                        APP_NAME,
                        f"Learning Site was updated from {installed or 'an unversioned version'} to {applied}.",
                    )
                elif installed:
                    p.current_version = installed
                    p.last_applied_upstream_tag = installed
                    self.manager.update(p)

            self.start("Synchronizing safely with your GitHub repository and official updates…", synchronize, sync_complete)
    def show_history(self):
        p=self.selected()
        if not p:return
        def action():
            return Repository(p.path()).run(["log", "--oneline", "-20"]).stdout
        def show(text):
            QMessageBox.information(self, "History", text or "No commits found.")
        self.start("Loading project history…", action, show)

    def delete_local_clone(self):
        project = self.selected()
        if not project:
            return
        target = project.path().resolve()
        answer = QMessageBox.warning(
            self,
            "Delete local project?",
            "This permanently deletes the local project folder:\n\n"
            f"{target}\n\n"
            "Your GitHub repository and all remote content will NOT be deleted. "
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        self.start("Deleting the local project folder…", lambda: self.manager.delete_local_clone(target))

    def configure_git_identity(self):
        """Optionally set commit identity in the selected repository only."""
        project = self.selected()
        if not project:
            return
        name, accepted = QInputDialog.getText(
            self,
            "Git identity for this site",
            "Author name (leave empty to keep the current setting):",
        )
        if not accepted:
            return
        email, accepted = QInputDialog.getText(
            self,
            "Git identity for this site",
            "Author email (leave empty to keep the current setting):",
        )
        if not accepted:
            return
        name, email = name.strip(), email.strip()
        if not name and not email:
            return

        def apply_identity():
            repo = Repository(project.path())
            if name:
                repo.run(["config", "--local", "user.name", name])
            if email:
                repo.run(["config", "--local", "user.email", email])

        self.start("Saving Git identity for this site…", apply_identity)

    def configure_project_settings(self):
        """Edit non-destructive settings stored for the selected project."""
        project = self.selected()
        if not project:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Project Settings — {project.display_name}")
        layout = QVBoxLayout(dialog)
        auto_push = QCheckBox("Push changes automatically after the editor closes")
        auto_push.setChecked(project.auto_push)
        layout.addWidget(auto_push)
        note = QLabel(
            "When disabled, changes are committed locally but remain on this computer "
            "until you choose Sync."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() != QDialog.Accepted:
            return
        project.auto_push = auto_push.isChecked()
        self.manager.update(project)
        self.refresh()
