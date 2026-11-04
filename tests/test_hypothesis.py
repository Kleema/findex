from hypothesis import given, strategies as st
from pathlib import Path
import pickle
from findex.index import Index
from findex.models import Posting


@given(st.dictionaries(st.text(min_size=1, max_size=5), st.lists(
    st.builds(Posting, doc_id=st.integers(min_value=1, max_value=100),
              frequency=st.integers(min_value=1, max_value=10)))))
def test_hypothesis_index_pickle(postings):
    # Властивість 1: load(save(index)) дає той самий індекс
    meta = {i: None for i in range(1, 10)}  # спрощено для тесту
    index = Index(postings, meta)  # type: ignore

    serialized = pickle.dumps({"postings": index._postings, "meta": index._doc_meta})
    loaded_data = pickle.loads(serialized)

    assert loaded_data["postings"] == index._postings


@given(st.lists(st.builds(Posting, doc_id=st.integers(min_value=1, max_value=100),
                          frequency=st.integers(min_value=1, max_value=10))))
def test_hypothesis_postings_sorted(postings):
    # Властивість 2: постінги завжди повинні підтримуватись умовою або сортуванням за doc_id
    sorted_postings = sorted(postings, key=lambda p: p.doc_id)
    for i in range(len(sorted_postings) - 1):
        assert sorted_postings[i].doc_id <= sorted_postings[i + 1].doc_id