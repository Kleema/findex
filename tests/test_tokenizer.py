from findex.tokenizer import tokenize

def test_tokenize_basic():
    tokens = list(tokenize("Hello World!"))
    assert tokens == ["hello", "world"]

def test_tokenize_hyphens_and_apostrophes():
    tokens = list(tokenize("Комп'ютер, будь-ласка, 2026-й рік."))
    assert tokens == ["комп'ютер", "будь-ласка", "2026-й", "рік"]

def test_tokenize_unicode_normalization():
    # Символ ﬃ (лігатура) має розбитись на ffi
    tokens = list(tokenize("eﬃcient"))
    assert tokens == ["efficient"]