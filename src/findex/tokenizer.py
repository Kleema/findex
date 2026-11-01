import re
import unicodedata
from typing import Iterator

# Дозволяємо літери, цифри, та слова з апострофом або дефісом всередині (напр. комп'ютер, хто-зна)
TOKEN_PATTERN = re.compile(r"\b[a-zа-яіїєґ0-9]+(?:['’-][a-zа-яіїєґ0-9]+)*\b")


def tokenize(text: str) -> Iterator[str]:
    """Генератор, що нормалізує текст та розбиває його на токени."""
    # Нормалізація Unicode (NFKC) та переведення в нижній регістр
    text = unicodedata.normalize('NFKC', text).lower()

    for match in TOKEN_PATTERN.finditer(text):
        yield match.group()