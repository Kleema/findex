import pickle
import time
import os
import psutil
from collections.abc import Mapping
from functools import cached_property
from contextlib import contextmanager
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from collections import defaultdict
import sys

from findex.models import Posting, DocMeta
from findex.tokenizer import tokenize


class Index(Mapping[str, list[Posting]]):
    def __init__(self, postings: dict[str, list[Posting]], doc_meta: dict[int, DocMeta]) -> None:
        self._postings = postings
        self._doc_meta = doc_meta

    def __getitem__(self, term: str) -> list[Posting]:
        return self._postings.get(term, [])

    def __iter__(self):
        return iter(self._postings)

    def __len__(self) -> int:
        return len(self._postings)

    def __contains__(self, term: object) -> bool:
        return term in self._postings

    def __repr__(self) -> str:
        return f"<Index vocab_size={len(self)} docs={self.num_docs}>"

    @cached_property
    def num_docs(self) -> int:
        return len(self._doc_meta)

    @cached_property
    def avg_doc_length(self) -> float:
        if not self.num_docs:
            return 0.0
        total_len = sum(meta.length for meta in self._doc_meta.values())
        return total_len / self.num_docs

    def df(self, term: str) -> int:
        return len(self[term])


@contextmanager
def open_index(filepath: str | Path):
    with open(filepath, 'rb') as f:
        data = pickle.load(f)
    index = Index(data["postings"], data["meta"])
    try:
        yield index
    finally:
        del index


def build_partial(paths: list[Path], start_doc_id: int) -> dict[str, dict]:
    postings: dict[str, list[Posting]] = defaultdict(list)
    doc_meta: dict[int, DocMeta] = {}
    doc_id = start_doc_id

    for filepath in paths:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        except Exception:
            continue

        tokens = list(tokenize(text))
        doc_meta[doc_id] = DocMeta(doc_id, filepath.name, len(tokens))

        term_positions: dict[str, list[int]] = defaultdict(list)
        for pos, term in enumerate(tokens):
            term_positions[term].append(pos)

        for term, positions in term_positions.items():
            postings[term].append(Posting(doc_id, len(positions), tuple(positions)))

        doc_id += 1

    return {"postings": dict(postings), "meta": doc_meta}


def merge_partials(partials: list[dict[str, dict]]) -> dict[str, dict]:
    merged_postings: dict[str, list[Posting]] = defaultdict(list)
    merged_meta: dict[int, DocMeta] = {}

    for p in partials:
        merged_meta.update(p["meta"])  # type: ignore
        for term, postings_list in p["postings"].items():  # type: ignore
            merged_postings[term].extend(postings_list)

    for term in merged_postings:
        merged_postings[term].sort(key=lambda x: x.doc_id)

    return {"postings": dict(merged_postings), "meta": merged_meta}


def build_index(corpus_dir: str | Path, out_path: str | Path, executor_type: str = "processes", workers: int = 1) -> \
dict[str, float]:
    corpus_path = Path(corpus_dir)
    files = [p for p in corpus_path.iterdir() if p.is_file() and p.suffix == '.txt']

    if not files:
        raise ValueError("Немає .txt файлів у корпусі")

    workers = max(1, workers)
    chunk_size = max(1, (len(files) + workers - 1) // workers)
    chunks = [files[i:i + chunk_size] for i in range(0, len(files), chunk_size)]

    start_ids = []
    curr_id = 1
    for chunk in chunks:
        start_ids.append(curr_id)
        curr_id += len(chunk)

    process = psutil.Process(os.getpid())
    t0 = time.perf_counter()
    c0 = time.process_time()

    partials = []
    if executor_type == "serial":
        for chunk, s_id in zip(chunks, start_ids):
            partials.append(build_partial(chunk, s_id))
    else:
        ExecutorClass = ProcessPoolExecutor if executor_type == "processes" else ThreadPoolExecutor
        with ExecutorClass(max_workers=workers) as executor:
            futures = [executor.submit(build_partial, chunk, s_id) for chunk, s_id in zip(chunks, start_ids)]
            for future in as_completed(futures):
                partials.append(future.result())

    t_merge_start = time.perf_counter()
    final_data = merge_partials(partials)
    t_merge_end = time.perf_counter()

    with open(out_path, 'wb') as f:
        pickle.dump(final_data, f)

    return {
        "wall_time": time.perf_counter() - t0,
        "cpu_time": time.process_time() - c0,
        "rss_mb": process.memory_info().rss / (1024 * 1024),
        "merge_time": t_merge_end - t_merge_start
    }