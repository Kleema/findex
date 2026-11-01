from pathlib import Path
from typing import Iterator, Tuple

def iter_documents(directory: Path | str) -> Iterator[Tuple[str, str]]:
    """Генератор, що читає текстові файли з директорії по одному."""
    dir_path = Path(directory)
    for file_path in dir_path.rglob("*.txt"):
        if file_path.is_file():
            # Використовуємо utf-8, ігноруємо помилки кодування для надійності
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                yield file_path.name, f.read()