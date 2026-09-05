import os
from pathlib import Path
from contextlib import contextmanager
from ..paths import ensure_data_directories

@contextmanager
def project_lock(project: Path):
    lock = ensure_data_directories() / "locks" / (str(abs(hash(str(project.resolve()))) ) + ".lock")
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY); os.write(fd, str(os.getpid()).encode()); os.close(fd)
    except FileExistsError as exc: raise RuntimeError("This project is already in use") from exc
    try: yield
    finally:
        try: lock.unlink()
        except FileNotFoundError: pass
