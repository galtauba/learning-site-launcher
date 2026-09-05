import json
from pathlib import Path

class TranslationManager:
    def __init__(self, language: str = "en"):
        self.language = language
        source = Path(__file__).with_name(f"{language}.json")
        self.values = json.loads(source.read_text(encoding="utf-8")) if source.exists() else {}
    def text(self, key: str, **values: str) -> str:
        return self.values.get(key, key).format(**values)
