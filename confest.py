import sys
from pathlib import Path

# Додаємо src до sys.path для коректного імпорту пакетів
sys.path.insert(0, str(Path(__file__).parent / "src"))