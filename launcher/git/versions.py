from dataclasses import dataclass
import re

@dataclass(frozen=True, order=True)
class StableTag:
    version: tuple[int, int, int]
    name: str
def stable_tags(names: list[str]) -> list[StableTag]:
    tags=[]
    for name in names:
        raw = name[1:] if name.startswith("v") else name
        match = re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", raw)
        if match: tags.append(StableTag(tuple(map(int, match.groups())), name))
    return sorted(tags, reverse=True)
