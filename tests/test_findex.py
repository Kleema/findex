import pytest
from pathlib import Path
from typer.testing import CliRunner
from findex.tokenizer import tokenize
from findex.cli import app
from findex.index import open_index, Index
from findex.scoring import BM25, TfIdf
from findex.parser import Term, And, Or, Not
from findex.search import search

runner = CliRunner()

@pytest.mark.parametrize("text,expected", [
    ("Hello, World!", ["hello", "world"]),
    ("Python 3.10 is awesome.", ["python", "3", "10", "is", "awesome"]),
    ("Unicode test: § café naïve", ["unicode", "test", "café", "naïve"]),
    ("", []),
])
def test_tokenizer(text: str, expected: list[str]):
    assert list(tokenize(text)) == expected

def test_index_build_and_stats(sample_index: Path):
    with open_index(sample_index) as idx:
        assert idx.num_docs == 3
        assert len(idx) > 0
        assert "python" in idx

def test_cli_stats(sample_index: Path):
    result = runner.invoke(app, ["stats", str(sample_index)])
    assert result.exit_code == 0
    assert "Кількість документів: 3" in result.output

@pytest.mark.slow
def test_cli_search_json(sample_index: Path):
    result = runner.invoke(app, ["search", str(sample_index), "python", "--json"])
    assert result.exit_code == 0
    assert "doc1.txt" in result.output or "doc2.txt" in result.output

def test_cli_missing_index():
    result = runner.invoke(app, ["search", "nonexistent.bin", "query"])
    assert result.exit_code != 0

def test_scorers_sanity():
    bm25 = BM25()
    tfidf = TfIdf()
    # Sanity checks з лабораторії 3
    score_bm25 = bm25.score(tf=2, df=1, num_docs=10, dl=100, avg_dl=200)
    score_tfidf = tfidf.score(tf=2, df=1, num_docs=10, dl=100, avg_dl=200)
    assert score_bm25 > 0
    assert score_tfidf > 0

def test_parser_trees(sample_index: Path):
    with open_index(sample_index) as idx:
        node1 = Term("python") & Term("programming")
        docs = node1.evaluate(idx)
        assert len(docs) > 0