import logging
from logging.handlers import RotatingFileHandler
from ..paths import ensure_data_directories

def configure_logging() -> logging.Logger:
    root = logging.getLogger("learning_site_launcher")
    if root.handlers:
        return root
    root.setLevel(logging.INFO)
    handler = RotatingFileHandler(ensure_data_directories() / "logs" / "launcher.log", maxBytes=1_000_000, backupCount=5, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root.addHandler(handler)
    return root
