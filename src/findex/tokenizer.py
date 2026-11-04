import re
import unicodedata
from collections.abc import Iterator


def tokenize(text: str) -> Iterator[str]:
    if not text:
        return

    # Явно замінюємо лігатури перед нормалізацією (наприклад, ﬃ -> ffi)
    ligatures = {
        "ﬃ": "ffi",
        "ﬄ": "ffl",
        "ﬀ": "ff",
        "ﬁ": "fi",
        "ﬂ": "fl",
    }
    for lig, replacement in ligatures.items():
        text = text.replace(lig, replacement)

    # Використовуємо NFC, щоб зберегти цілісність діакритичних знаків та літер (café, naïve, й)
    normalized = unicodedata.normalize("NFC", text)

    # Патерн: слова/числа, що можуть містити внутрішні апострофи або дефіси, але розділені крапками та пробілами
    pattern = r"\w+(?:['\-]\w+)*"

    for match in re.finditer(pattern, normalized):
        yield match.group(0).lower()