import urllib.request
from pathlib import Path

# Вказуємо шлях до папки корпусу та створюємо її, якщо немає
corpus_dir = Path("data/corpus")
corpus_dir.mkdir(parents=True, exist_ok=True)

# Прямі посилання на великі текстові файли з Project Gutenberg
books = {
    "shakespeare.txt": "https://www.gutenberg.org/cache/epub/100/pg100.txt",          # ~5.5 MB
    "war_and_peace.txt": "https://www.gutenberg.org/cache/epub/2600/pg2600.txt",      # ~3.3 MB
    "webster_dictionary.txt": "https://www.gutenberg.org/cache/epub/29765/pg29765.txt", # ~27.5 MB
    "monte_cristo.txt": "https://www.gutenberg.org/cache/epub/1184/pg1184.txt",       # ~2.7 MB
    "les_miserables.txt": "https://www.gutenberg.org/cache/epub/135/pg135.txt"        # ~3.3 MB
}

print("Починаємо завантаження корпусу...")
for filename, url in books.items():
    filepath = corpus_dir / filename
    if not filepath.exists():
        print(f"Завантаження {filename}...")
        try:
            # Завантажуємо файл за посиланням
            urllib.request.urlretrieve(url, filepath)
            print(f"✓ {filename} збережено.")
        except Exception as e:
            print(f"Помилка завантаження {filename}: {e}")
    else:
        print(f"✓ {filename} вже існує, пропускаємо.")

print("\nУсі файли успішно завантажені у data/corpus!")