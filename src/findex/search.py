import heapq
import functools
from pathlib import Path
from findex.index import open_index
from findex.scoring import BM25, TfIdf
from findex.models import SearchResult
from findex.parser import Term, And, Or, Not
from findex.utils import timed
from findex.tokenizer import tokenize


def get_snippet(filepath: Path, term: str, radius: int = 80) -> str:
    if not filepath.exists():
        return ""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
    except Exception:
        return ""

    idx = text.lower().find(term.lower())
    if idx == -1:
        return text[:radius * 2] + "..."
    start = max(0, idx - radius)
    end = min(len(text), idx + len(term) + radius)
    return f"...{text[start:idx]}[{text[idx:idx + len(term)]}]{text[idx + len(term):end]}..."


def cached_evaluate(query_str: str, index) -> set[int]:
    """Внутренняя функция с lru_cache, которая кеширует результат по строке запроса,
    не передавая нехешованый объект index напрямую в декоратор."""

    @functools.lru_cache(maxsize=128)
    def _evaluate_memo(q: str):
        terms = list(tokenize(q))
        if not terms:
            return frozenset()
        node = Term(terms[0])
        for t in terms[1:]:
            node = node & Term(t)
        return frozenset(node.evaluate(index))

    return set(_evaluate_memo(query_str))


@timed
def search(query: str, index, scorer, corpus_dir: Path, top_k: int = 5) -> list[SearchResult]:
    matched_docs = cached_evaluate(query, index)
    terms = list(tokenize(query))

    heap = []
    for doc_id in matched_docs:
        doc_score = 0.0
        dl = index._doc_meta[doc_id].length

        for term in terms:
            postings = index[term]
            p = next((post for post in postings if post.doc_id == doc_id), None)
            if p:
                doc_score += scorer.score(p.frequency, index.df(term), index.num_docs, dl, index.avg_doc_length)

        doc_name = index._doc_meta[doc_id].name
        snippet = get_snippet(corpus_dir / doc_name, terms[0] if terms else "")

        # Сохраняем отрицательный score для max-heap в heapq (по умолчанию в Python min-heap)
        heapq.heappush(heap, SearchResult(score=-doc_score, doc_id=doc_id, name=doc_name, snippet=snippet))

    results = []
    for _ in range(min(top_k, len(heap))):
        res = heapq.heappop(heap)
        results.append(SearchResult(score=-res.score, doc_id=res.doc_id, name=res.name, snippet=res.snippet))
    return results


if __name__ == "__main__":
    corpus = Path("data/corpus")
    with open_index("index.bin") as idx:
        print(f"Індекс завантажено: {idx}")

        # Перший запит
        print("\n--- Перший запит ---")
        res1 = search("prince war", idx, BM25(), corpus)

        # Повторний запит (тут спрацює lru_cache і ви побачите швидкий час виконання)
        print("\n--- Повторний запит (кеш) ---")
        res2 = search("prince war", idx, BM25(), corpus)

        print("\nРезультати пошуку:")
        for r in res1:
            print(f"[{r.score:.4f}] {r.name}\nSnippet: {r.snippet}\n")