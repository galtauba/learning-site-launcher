from pathlib import Path

APP_NAME = "Learning Site Launcher"
OFFICIAL_LEARNING_SITE_REPOSITORY = "https://github.com/galtauba/LearningSite"
OFFICIAL_LEARNING_SITE_GIT_URL = f"{OFFICIAL_LEARNING_SITE_REPOSITORY}.git"
GIT_DOWNLOAD_URL = "https://git-scm.com/download/win"
GITHUB_API = "https://api.github.com"
REQUIRED_PATHS = ("main.py", "public", "public/index.html", "public/content")
DEFAULT_METADATA = {"editorEntry": "main.py", "siteRoot": "public", "minimumLauncherVersion": "1.0.0"}

def app_data_dir() -> Path:
    return Path.home() / "AppData" / "Local" / "LearningSiteLauncher"

def default_projects_dir() -> Path:
    return Path.home() / "Documents" / "Learning Sites"
