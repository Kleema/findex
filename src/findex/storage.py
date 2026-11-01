import pickle
import json
from pathlib import Path
from typing import Any

def save_index_pickle(index_data: Any, filepath: str | Path):
    with open(filepath, 'wb') as f:
        pickle.dump(index_data, f)

def load_index_pickle(filepath: str | Path) -> Any:
    with open(filepath, 'rb') as f:
        return pickle.load(f)

# Альтернативний формат (JSON) для порівняння розмірів
def save_index_json(index_data: Any, filepath: str | Path):
    # JSON не вміє зберігати об'єкти класів без кастомного енкодера
    # Тому тут ми б конвертували Posting у словники, що займає більше місця
    pass