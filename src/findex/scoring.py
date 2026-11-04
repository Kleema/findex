import numpy as np
from findex.index import Index


class BM25:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def score(self, query_tokens_or_tf=None, index: Index = None, **kwargs) -> np.ndarray:
        # Підтримка старої сигнатури з тестів (standalone tf/idf)
        if index is None and isinstance(query_tokens_or_tf, (int, float, np.ndarray)):
            tf = query_tokens_or_tf
            if isinstance(tf, np.ndarray) and tf.size == 0:
                return tf
            idf = kwargs.get("idf", 1.0)
            length = kwargs.get("length", 10.0)
            avgdl = kwargs.get("avgdl", 10.0)
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (length / avgdl if avgdl > 0 else 1.0))
            return idf * (numerator / denominator)

        if index is None:
            return np.array([], dtype=np.float32)

        query_tokens = query_tokens_or_tf
        num_docs = index.num_docs
        if num_docs == 0 or not query_tokens:
            return np.array([], dtype=np.float32)

        scores = np.zeros(num_docs, dtype=np.float32)
        avgdl = index.avg_doc_length

        for term in query_tokens:
            postings = index[term]
            if not postings:
                continue

            df = len(postings)
            idf = np.log((num_docs - df + 0.5) / (df + 0.5) + 1.0)
            idf = max(0.0, idf)

            for p in postings:
                doc_id = p.doc_id
                freq = p.freq
                doc_len = index._doc_meta[doc_id].length

                numerator = freq * (self.k1 + 1)
                denominator = freq + self.k1 * (1 - self.b + self.b * (doc_len / avgdl if avgdl > 0 else 1))
                scores[doc_id - 1] += idf * (numerator / denominator)

        return scores


class TfIdf:
    def score(self, query_tokens_or_tf=None, index: Index = None, **kwargs) -> np.ndarray:
        if index is None and isinstance(query_tokens_or_tf, (int, float, np.ndarray)):
            tf = query_tokens_or_tf
            if isinstance(tf, np.ndarray) and tf.size == 0:
                return tf
            idf = kwargs.get("idf", 1.0)
            return tf * idf

        if index is None:
            return np.array([], dtype=np.float32)

        query_tokens = query_tokens_or_tf
        num_docs = index.num_docs
        if num_docs == 0 or not query_tokens:
            return np.array([], dtype=np.float32)

        scores = np.zeros(num_docs, dtype=np.float32)

        for term in query_tokens:
            postings = index[term]
            if not postings:
                continue

            df = len(postings)
            idf = np.log(num_docs / df) if df > 0 else 0.0

            for p in postings:
                doc_id = p.doc_id
                freq = p.freq
                scores[doc_id - 1] += freq * idf

        return scores