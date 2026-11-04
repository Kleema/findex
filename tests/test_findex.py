import pytest
from pathlib import Path
from typer.testing import CliRunner
from findex.cli import app
from findex.tokenizer import tokenize
from findex.scoring import BM25, TfIdf
from typer.testing import CliRunner


runner = CliRunner()

@pytest.mark.parametrize("text,expected", [
    ("Hello, World!", ["hello", "world"]),
    ("Python 3.10 is awesome.", ["python", "3", "10", "is", "awesome"]),
    ("Unicode test: § café naïve", ["unicode", "test", "café", "naïve"]),
    ("", []),
])
def test_tokenizer(text: str, expected: list[str]):
    assert list(tokenize(text)) == expected

def test_tokenize_hyphens_and_apostrophes():
    tokens = list(tokenize("Комп'ютер, будь-ласка, 2026-й рік."))
    assert tokens == ["комп'ютер", "будь-ласка", "2026-й", "рік"]

def test_tokenize_unicode_normalization():
    tokens = list(tokenize("eﬃcient"))
    assert tokens == ["efficient"]

def test_cli_missing_index():
    result = runner.invoke(app, ["search", "nonexistent.bin", "query"])
    assert result.exit_code != 0

def test_scorers_sanity():
    bm25 = BM25()
    tfidf = TfIdf()
    assert bm25 is not None
    assert tfidf is not None