import pytest
from pathlib import Path
from findex.index import build_partial, merge_partials, build_index


def test_sequential_merge_equivalence(small_corpus: Path, tmp_path: Path):
    files = list(small_corpus.glob("*.txt"))

    serial_out = tmp_path / "serial.bin"
    build_index(small_corpus, serial_out, executor_type="serial", workers=1)

    partial = build_partial(files, 1)
    merged = merge_partials([partial])

    assert len(merged["meta"]) == 3
    assert "python" in merged["postings"]
    assert [p.doc_id for p in merged["postings"]["python"]] == [1, 2]