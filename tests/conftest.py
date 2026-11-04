import pytest
from pathlib import Path
from findex.index import build_index


@pytest.fixture
def small_corpus(tmp_path: Path) -> Path:
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()

    (corpus_dir / "doc1.txt").write_text("computer science engineering python programming", encoding="utf-8")
    (corpus_dir / "doc2.txt").write_text("python programming language and data science", encoding="utf-8")
    (corpus_dir / "doc3.txt").write_text("advanced computer architecture and digital logic", encoding="utf-8")

    return corpus_dir


@pytest.fixture
def sample_index(small_corpus: Path, tmp_path: Path) -> Path:
    out_bin = tmp_path / "index.bin"
    build_index(str(small_corpus), str(out_bin))
    return out_bin