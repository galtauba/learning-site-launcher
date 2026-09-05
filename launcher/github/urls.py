import re
from urllib.parse import urlparse

_SSH = re.compile(r"^(?:git@)?github\.com:([^/\s]+)/([^/\s]+?)(?:\.git)?$")
def github_owner_repo(url: str) -> tuple[str, str] | None:
    m=_SSH.match(url)
    if m: return m.group(1), m.group(2)
    p=urlparse(url)
    if p.hostname != "github.com": return None
    pieces=p.path.strip("/").split("/")
    return (pieces[0], pieces[1].removesuffix(".git")) if len(pieces)==2 and all(pieces) else None
def github_web_url(url: str) -> str | None:
    parsed=github_owner_repo(url)
    return f"https://github.com/{parsed[0]}/{parsed[1]}" if parsed else None
