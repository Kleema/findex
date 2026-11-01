from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Posting:
    """Клас для зберігання інформації про термін у документі."""
    doc_id: int
    frequency: int

@dataclass(frozen=True, slots=True)
class DocMeta:
    """Метадані документа."""
    doc_id: int
    name: str
    length: int