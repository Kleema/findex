from dataclasses import dataclass, field
from typing import Tuple

@dataclass(frozen=True, slots=True)
class Posting:
    doc_id: int
    frequency: int
    positions: Tuple[int, ...] = field(default_factory=tuple)

@dataclass(frozen=True, slots=True)
class DocMeta:
    doc_id: int
    name: str
    length: int

@dataclass(order=True, slots=True)
class SearchResult:
    score: float
    doc_id: int = field(compare=False)
    name: str = field(compare=False)
    snippet: str = field(compare=False)