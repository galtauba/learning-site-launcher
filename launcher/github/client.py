import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from .urls import github_owner_repo
from ..constants import GITHUB_API

class GitHubClient:
    def repository(self, url: str) -> dict | None:
        identity=github_owner_repo(url)
        if not identity: return None
        request=Request(f"{GITHUB_API}/repos/{identity[0]}/{identity[1]}", headers={"Accept":"application/vnd.github+json", "User-Agent":"LearningSiteLauncher"})
        try:
            with urlopen(request, timeout=15) as response: return json.load(response)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError): return None
    def root_clone_url(self, url: str) -> str | None:
        data=self.repository(url)
        if not data: return None
        root=data.get("source") or data.get("parent") or data
        return root.get("clone_url") if isinstance(root, dict) else None
