import subprocess
from pathlib import Path
def launch_replacement(installer: Path) -> None:
    subprocess.Popen([str(installer)], close_fds=True)
