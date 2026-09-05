from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

class ProjectState(str, Enum):
    UNKNOWN="UNKNOWN"; READY="READY"; DIRTY="DIRTY"; LOCAL_AHEAD="LOCAL_AHEAD"; REMOTE_AHEAD="REMOTE_AHEAD"; DIVERGED="DIVERGED"; UPSTREAM_UPDATE_AVAILABLE="UPSTREAM_UPDATE_AVAILABLE"; UPDATING="UPDATING"; CONFLICT="CONFLICT"; OFFLINE="OFFLINE"; AUTH_REQUIRED="AUTH_REQUIRED"; EDITOR_RUNNING="EDITOR_RUNNING"; ERROR="ERROR"

@dataclass
class Project:
    display_name: str
    local_path: str
    origin_url: str
    upstream_url: str = ""
    branch: str = "main"
    current_version: str = "Unversioned / Legacy"
    last_applied_upstream_tag: str = ""
    last_applied_upstream_commit: str = ""
    last_successful_push_commit: str = ""
    last_sync: str = ""
    last_editor_open: str = ""
    auto_updates: bool = True
    auto_push: bool = True
    trusted: bool = False
    state: str = ProjectState.UNKNOWN.value
    def path(self) -> Path: return Path(self.local_path)
    def to_dict(self) -> dict[str, Any]: return asdict(self)
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Project":
        fields = {key: value for key, value in data.items() if key in cls.__dataclass_fields__}
        return cls(**fields)
