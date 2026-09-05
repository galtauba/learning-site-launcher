# Learning Site Launcher

Learning Site Launcher is a Windows 10/11 desktop application for safely managing multiple forks of [Learning Site](https://github.com/galtauba/LearningSite). It uses the user's installed Git for Windows and Git Credential Manager; it never stores GitHub passwords or personal-access tokens.

## Users

Requirements: Windows 10/11 x64, Git for Windows, a GitHub account, and a fork of Learning Site. Install Git, download `LearningSiteLauncher.exe`, open it, choose **Add Site**, paste the fork URL, and select **Open Editor**. Git Credential Manager may open a browser for normal GitHub authentication. Each editor session is committed and pushed automatically when enabled. Stable upstream tags are fetched from the official repository; untagged and prerelease updates are not installed automatically. A push to a connected fork lets Cloudflare Pages deploy normally.

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

The official upstream is defined once in `launcher/constants.py`. The project registry and logs live in `%LOCALAPPDATA%\LearningSiteLauncher`; clones default to `%USERPROFILE%\Documents\Learning Sites`.

## Architecture

`launcher/git` invokes the installed Git executable and enforces no-force/no-hard-reset workflows. `launcher/projects` provides validation, trust state, atomic registry writes, and locks. `launcher/editor` runs the external editor in a separate launcher process mode. `launcher/ui` is the PySide6 interface. `launcher/diagnostics` exports sanitized reports and `launcher/updater` verifies downloaded SHA-256 values before an installer is launched.

## Releases

Tag the version (for example `v1.0.0`). GitHub Actions runs tests, builds the EXE, calculates SHA-256, and creates a release. The tag should match `launcher/version.py`.
