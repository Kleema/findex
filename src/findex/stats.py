import tracemalloc
import time
from collections import Counter
from pathlib import Path
from typing import Dict, Any

from findex.document import iter_documents
from findex.tokenizer import tokenize

def gather_stats_lazy(corpus_dir: Path | str) -> Dict[str, Any]:
    """Використовує генератори: мінімальне споживання пам'яті."""
    tracemalloc.start()
    start_time = time.perf_counter()

    doc_count, token_count = 0, 0
    vocab = Counter()

    for name, text in iter_documents(corpus_dir):
        doc_count += 1
        for token in tokenize(text):
            token_count += 1
            vocab[token] += 1

    end_time = time.perf_counter()
    _, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "strategy": "Lazy (Generators)",
        "time_sec": end_time - start_time,
        "peak_memory_mb": peak_memory / (1024 * 1024),
        "docs": doc_count,
        "tokens": token_count,
        "vocab_size": len(vocab),
        "top_5": vocab.most_common(5) # Для виводу скоротимо до 5
    }

def gather_stats_greedy(corpus_dir: Path | str) -> Dict[str, Any]:
    """Жадібний метод: завантажує всі тексти та токени в списки."""
    tracemalloc.start()
    start_time = time.perf_counter()

    doc_count, token_count = 0, 0
    vocab = Counter()

    # 1. Завантажуємо ВСІ документи в список
    dir_path = Path(corpus_dir)
    documents = [f.read_text(encoding="utf-8", errors="ignore")
                 for f in dir_path.rglob("*.txt") if f.is_file()]
    doc_count = len(documents)

    # 2. Зберігаємо ВСІ токени в список
    all_tokens = []
    for text in documents:
        all_tokens.extend(list(tokenize(text)))

    # 3. Рахуємо статистику
    for token in all_tokens:
        token_count += 1
        vocab[token] += 1

    end_time = time.perf_counter()
    _, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "strategy": "Greedy (Lists)",
        "time_sec": end_time - start_time,
        "peak_memory_mb": peak_memory / (1024 * 1024),
        "docs": doc_count,
        "tokens": token_count,
        "vocab_size": len(vocab),
        "top_5": vocab.most_common(5)
    }