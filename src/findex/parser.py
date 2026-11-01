from abc import ABC, abstractmethod

class Node(ABC):
    @abstractmethod
    def evaluate(self, index) -> set[int]: ...

    def __and__(self, other): return And(self, other)
    def __or__(self, other): return Or(self, other)
    def __invert__(self): return Not(self)

class Term(Node):
    def __init__(self, term: str):
        self.term = term
    def evaluate(self, index) -> set[int]:
        return {p.doc_id for p in index[self.term]}

class Phrase(Node):
    def __init__(self, terms: list[str]):
        self.terms = terms
    def evaluate(self, index) -> set[int]:
        if not self.terms: return set()
        # Базова реалізація: перетин (AND) для слів фрази.
        # Для точних позицій потрібна складніша логіка зчитування p.positions
        docs = {p.doc_id for p in index[self.terms[0]]}
        for term in self.terms[1:]:
            docs &= {p.doc_id for p in index[term]}
        return docs

class And(Node):
    def __init__(self, left: Node, right: Node):
        self.left, self.right = left, right
    def evaluate(self, index) -> set[int]:
        return self.left.evaluate(index) & self.right.evaluate(index)

class Or(Node):
    def __init__(self, left: Node, right: Node):
        self.left, self.right = left, right
    def evaluate(self, index) -> set[int]:
        return self.left.evaluate(index) | self.right.evaluate(index)

class Not(Node):
    def __init__(self, child: Node):
        self.child = child
    def evaluate(self, index) -> set[int]:
        all_docs = set(index._doc_meta.keys())
        return all_docs - self.child.evaluate(index)