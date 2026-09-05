from pathlib import Path
from urllib.request import urlretrieve
def download(url: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True,exist_ok=True); urlretrieve(url,destination); return destination
