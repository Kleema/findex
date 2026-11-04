from pathlib import Path
import numpy as np
from findex.index import Index
from findex.models import SearchResult
from findex.tokenizer import tokenize


def get_snippet(corpus_path: Path, name: str, query_tokens: list[str]) -> str:
    text = ""
    file_path = corpus_path / name
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        except Exception:
            pass

    if not text:
        return "..."

    lower_text = text.lower()
    for token in query_tokens:
        pos = lower_text.find(token)
        if pos != -1:
            start = max(0, pos - 50)
            end = min(len(text), pos + 100)
            snippet = text[start:end].replace("\n", " ")
            return f"...{snippet}..."

    return text[:150].replace("\n", " ") + "..."


def search(query: str, index: Index, scorer, corpus_path: Path, top_k: int = 5) -> list[SearchResult]:
    query_tokens = list(tokenize(query))
    if not query_tokens or index.num_docs == 0:
        return []

    scores = scorer.score(query_tokens, index)
    if len(scores) == 0:
        return []

    k = min(top_k, len(scores))
    if k <= 0:
        return []

    part_indices = np.argpartition(scores, -k)[-k:]
    top_indices = part_indices[np.argsort(scores[part_indices])[::-1]]

    results = []
    for idx_val in top_indices:
        score = float(scores[idx_val])
        if score <= 0:
            continue
        doc_id = int(idx_val + 1)
        if doc_id not in index._doc_meta:
            continue
        meta = index._doc_meta[doc_id]

        snippet = get_snippet(corpus_path, meta.name, query_tokens)
        results.append(SearchResult(doc_id=doc_id, name=meta.name, score=score, snippet=snippet))

    return results