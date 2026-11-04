import pytest
from fastapi.testclient import TestClient
from findex.web.app import app, get_index
from findex.index import Index
from findex.models import DocMeta

class MockIndex(Index):
    def __init__(self):
        self._postings = {"test": []}
        self._doc_meta = {1: DocMeta(1, "doc1.txt", 10)}

client = TestClient(app)

def test_health_no_index():
    app.dependency_overrides[get_index] = lambda: None
    response = client.get("/health")
    assert response.status_code == 503

def test_health_with_index():
    app.dependency_overrides[get_index] = lambda: MockIndex()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_get_document_404():
    app.dependency_overrides[get_index] = lambda: MockIndex()
    response = client.get("/docs/999")
    assert response.status_code == 404