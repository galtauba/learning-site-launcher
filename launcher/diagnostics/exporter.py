import json, zipfile
from pathlib import Path
from .collector import collect
from ..logging.sanitizer import sanitize
from ..paths import ensure_data_directories

def export_report(destination: Path, project: Path | None = None) -> Path:
    report={k:sanitize(str(v)) for k,v in collect(project).items()}
    with zipfile.ZipFile(destination,"w",zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("diagnostics.json", json.dumps(report, indent=2))
        logfile=ensure_data_directories()/"logs"/"launcher.log"
        if logfile.exists(): archive.writestr("launcher.log", sanitize(logfile.read_text(encoding="utf-8", errors="replace")))
    return destination
