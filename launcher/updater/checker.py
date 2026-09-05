import json
from urllib.request import Request,urlopen
from ..constants import OFFICIAL_LEARNING_SITE_REPOSITORY
def latest_launcher_release(repository: str) -> dict | None:
    request=Request(f"https://api.github.com/repos/{repository}/releases/latest",headers={"Accept":"application/vnd.github+json","User-Agent":"LearningSiteLauncher"})
    try:
        with urlopen(request,timeout=15) as response: return json.load(response)
    except Exception: return None
