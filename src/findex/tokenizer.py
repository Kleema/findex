import re
from typing import Iterable

def tokenize(text: str) -> Iterable[str]:
    # Регулярний вираз для пошуку слів
    words = re.findall(r"\b\w+\b", text.lower())
    for word in words:
        yield word