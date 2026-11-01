import argparse
import tracemalloc
import time
from findex.tokenizer import tokenize
from findex.storage import load_index_pickle


def intersect_merge(p1: list, p2: list) -> list:
    """Двовказівниковий алгоритм перетину двох відсортованих списків."""
    result = []
    i, j = 0, 0
    while i < len(p1) and j < len(p2):
        if p1[i].doc_id == p2[j].doc_id:
            result.append(p1[i])
            i += 1
            j += 1
        elif p1[i].doc_id < p2[j].doc_id:
            i += 1
        else:
            j += 1
    return result


def search_merge(query_terms: list, index: dict) -> list:
    if not query_terms: return []
    # Сортуємо терміни за довжиною постінгів (оптимізація запиту)
    query_terms.sort(key=lambda t: len(index.get(t, [])))

    result = index.get(query_terms[0], [])
    for term in query_terms[1:]:
        result = intersect_merge(result, index.get(term, []))
        if not result: break
    return result


def search_set(query_terms: list, index: dict) -> list:
    if not query_terms: return []
    # Збираємо множини doc_id для кожного терміну
    sets = [{p.doc_id for p in index.get(term, [])} for term in query_terms]
    # Перетин усіх множин
    common_doc_ids = set.intersection(*sets) if sets else set()

    # Відновлюємо оригінальні об'єкти Posting для результату
    return [p for p in index.get(query_terms[0], []) if p.doc_id in common_doc_ids]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search in inverted index")
    parser.add_argument("index_file", help="Path to index file")
    parser.add_argument("query", help="Query string")
    parser.add_argument("--engine", choices=["merge", "set"], default="merge")
    args = parser.parse_args()

    tracemalloc.start()
    start_time = time.perf_counter()

    data = load_index_pickle(args.index_file)
    postings = data["postings"]
    meta = data["meta"]

    query_terms = list(tokenize(args.query))

    if args.engine == "merge":
        results = search_merge(query_terms, postings)
    else:
        results = search_set(query_terms, postings)

    end_time = time.perf_counter()
    _, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"Query: '{args.query}' | Engine: {args.engine}")
    print(f"Found {len(results)} documents:")
    for p in results:
        doc_name = meta[p.doc_id].name
        print(f" - {doc_name} (freq: {p.frequency})")

    print(f"\nSearch time: {end_time - start_time:.6f} sec")
    print(f"Peak search memory: {peak_memory / (1024 * 1024):.4f} MB")