import argparse
import tracemalloc
import time
from collections import defaultdict, Counter
from pathlib import Path

# Імпорти з вашої Лаби 1
from findex.document import iter_documents
from findex.tokenizer import tokenize
from findex.models import Posting, DocMeta
from findex.storage import save_index_pickle


class InvertedIndex:
    def __init__(self):
        self.postings = defaultdict(list)
        self.doc_meta = {}
        self._next_doc_id = 1

    def build(self, corpus_dir: str):
        for filename, text in iter_documents(corpus_dir):
            doc_id = self._next_doc_id
            self._next_doc_id += 1

            tokens = list(tokenize(text))
            self.doc_meta[doc_id] = DocMeta(doc_id=doc_id, name=filename, length=len(tokens))

            term_freqs = Counter(tokens)
            for term, freq in term_freqs.items():
                self.postings[term].append(Posting(doc_id=doc_id, frequency=freq))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build inverted index")
    parser.add_argument("corpus_dir", help="Path to corpus directory")
    parser.add_argument("--out", required=True, help="Output index file")
    args = parser.parse_args()

    tracemalloc.start()
    start_time = time.perf_counter()

    index = InvertedIndex()
    index.build(args.corpus_dir)
    save_index_pickle({"postings": index.postings, "meta": index.doc_meta}, args.out)

    end_time = time.perf_counter()
    _, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"Index built and saved to {args.out}")
    print(f"Time taken: {end_time - start_time:.4f} seconds")
    print(f"Peak memory: {peak_memory / (1024 * 1024):.4f} MB")