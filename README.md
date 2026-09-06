# Learning Site Launcher

Learning Site Launcher is a Windows 10/11 desktop application for safely managing [Learning Site](https://github.com/galtauba/LearningSite) projects. It uses the user's installed Git for Windows and Git Credential Manager; it never stores GitHub passwords or personal-access tokens.

## Users

Requirements: Windows 10/11 x64, Git for Windows, and a GitHub account. End users do not need a separate Python installation: the packaged EXE provides its own runtime. Git Credential Manager may open a browser for normal GitHub authentication.

### Add a site

Choose **Add Site** and paste a GitHub HTTPS or SSH repository URL.

- A normal Learning Site fork is configured with the user's repository as `origin` and the official project as read-only `upstream`.
- If the repository is empty, the Launcher offers to initialize it from the official Learning Site history. The initial content is pushed to the user's `origin`; future official updates can therefore be merged safely.
- An existing local repository can be added with **Add Existing Local Project**. A repository is trusted automatically only when the Launcher can verify its relationship to the official project through Git history. Unverified repositories cannot run `main.py` until they are verified/trusted.

### Editing and synchronization

Select a site and choose **Open Editor**. Before opening it, the Launcher synchronizes the user's `origin` and checks the official `upstream` for stable version tags. If a newer stable release is available, it asks whether to install the update before opening the editor.

After the editor closes, local changes are committed and, when enabled, pushed to `origin`. The Launcher never pushes to the official upstream, force-pushes, resets hard, or silently discards user work. Untagged upstream commits and prerelease tags such as `beta` or `rc` are not installed automatically. A push to a connected repository lets Cloudflare Pages deploy normally.

### Per-site Git identity

Choose **Git Identity** for a selected site to set the author name and/or email used for that site’s commits. These values are saved with `git config --local` in the site's `.git/config`; global Git identity settings and other sites are unchanged.

### Remove a local site

**Delete Local Clone** permanently removes only the selected local project folder after confirmation. It never deletes the GitHub repository or remote content.

## Development

Use Python 3.12+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m launcher
python -m pytest
.\scripts\build.ps1
```

The official upstream is defined once in `launcher/constants.py`. The project registry and logs live in `%LOCALAPPDATA%\LearningSiteLauncher`; clones default to `%USERPROFILE%\Documents\Learning Sites`. Run the development command from the Launcher repository root; external editors are started from their own project directories by the Launcher.

## Architecture

`launcher/git` invokes the installed Git executable and enforces no-force/no-hard-reset workflows, origin synchronization, recovery commits, checkpoint branches, and stable upstream-tag updates. `launcher/projects` provides validation, trust state, atomic registry writes, local-clone deletion, and locks. `launcher/editor` runs the external editor in a separate launcher process so it has its own Qt application instance. `launcher/ui` is the PySide6 interface. `launcher/diagnostics` exports sanitized reports and `launcher/updater` verifies downloaded SHA-256 values before an installer is launched.

## Releases

Build and publish releases manually. Run `python -m pytest`, then `./scripts/build.ps1`; the EXE is written to `dist/LearningSiteLauncher.exe`. Run `./scripts/release.ps1` to run tests, build the EXE, and generate `dist/LearningSiteLauncher.exe.sha256`. The release tag, when used, should match `launcher/version.py`.
