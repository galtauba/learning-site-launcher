import re

_URL_CREDENTIALS = re.compile(r"(https?://)([^/@:\s]+):([^@/\s]+)@")
_AUTH = re.compile(r"(?i)(authorization:\s*(?:bearer|token|basic)\s+)[^\s]+")

def sanitize(value: str) -> str:
    """Remove URL userinfo and authorization values before logs leave memory."""
    value = _URL_CREDENTIALS.sub(r"\1***:***@", value)
    return _AUTH.sub(r"\1***", value)
