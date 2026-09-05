from dataclasses import dataclass
from pathlib import Path
from ..constants import REQUIRED_PATHS

@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    missing: tuple[str, ...] = ()

def validate_learning_site(root: Path) -> ValidationResult:
    missing = tuple(item for item in REQUIRED_PATHS if not (root / item).exists())
    return ValidationResult(not missing, missing)
