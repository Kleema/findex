import math
from typing import Protocol

class Scorer(Protocol):
    def score(self, tf: int, df: int, num_docs: int, dl: int, avg_dl: float) -> float: ...

class TfIdf:
    def score(self, tf: int, df: int, num_docs: int, dl: int, avg_dl: float) -> float:
        idf: float = math.log((num_docs + 1) / (df + 1)) + 1
        return float(tf * idf)

class BM25:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1: float = k1
        self.b: float = b

    def score(self, tf: int, df: int, num_docs: int, dl: int, avg_dl: float) -> float:
        idf: float = math.log((num_docs - df + 0.5) / (df + 0.5) + 1)
        term_freq_norm: float = (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * (dl / avg_dl)))
        return float(idf * term_freq_norm)
