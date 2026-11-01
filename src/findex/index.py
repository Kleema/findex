import pickle
from collections.abc import Mapping
from functools import cached_property
from contextlib import contextmanager
from pathlib import Path
from findex.models import Posting, DocMeta
from findex.utils import timed


class Index(Mapping):
    def __init__(self, postings: dict[str, list[Posting]], doc_meta: dict[int, DocMeta]):
        self._postings = postings
        self._doc_meta = doc_meta

    def __getitem__(self, term: str) -> list[Posting]:
        return self._postings.get(term, [])

    def __iter__(self):
        return iter(self._postings)

    def __len__(self):
        return len(self._postings)

    def __contains__(self, term: object) -> bool:
        return term in self._postings

    def __repr__(self):
        return f"<Index vocab_size={len(self)} docs={self.num_docs}>"

    @cached_property
    def num_docs(self) -> int:
        return len(self._doc_meta)

    @cached_property
    def avg_doc_length(self) -> float:
        if not self.num_docs: return 0.0
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
        del index  # Звільнення ресурсів


@timed
def build_index(corpus_dir: str, out_path: str):
    from findex.document import iter_documents
    from findex.tokenizer import tokenize
    from collections import defaultdict

    postings = defaultdict(list)
    doc_meta = {}
    doc_id = 1

    for filename, text in iter_documents(corpus_dir):
        tokens = list(tokenize(text))
        doc_meta[doc_id] = DocMeta(doc_id, filename, len(tokens))

        # Збирання позицій
        term_positions = defaultdict(list)
        for pos, term in enumerate(tokens):
            term_positions[term].append(pos)

        for term, positions in term_positions.items():
            postings[term].append(Posting(doc_id, len(positions), tuple(positions)))
        doc_id += 1

    with open(out_path, 'wb') as f:
        pickle.dump({"postings": dict(postings), "meta": doc_meta}, f)