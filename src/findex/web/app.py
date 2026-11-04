import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from findex.config import settings
from findex.index import open_index, Index
from findex.scoring import BM25, TfIdf
from findex.search import search
from findex.models import SearchResult

logger = logging.getLogger(__name__)

# Глобальний стан індексу
index_instance: Index | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global index_instance
    if settings.index_path.exists():
        try:
            with open_index(settings.index_path) as idx:
                index_instance = idx
            logger.info(f"Індекс успішно завантажено з {settings.index_path}")
        except Exception as e:
            logger.error(f"Помилка завантаження індексу: {e}")
    yield
    index_instance = None

app = FastAPI(title="Findex Web Search", version="0.7.0", lifespan=lifespan)

# Налаштування шаблонів та вимкнення кешу для сумісності з Jinja2
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))
templates.env.cache = None

def get_index() -> Index:
    if index_instance is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Індекс ще не завантажений або недоступний"
        )
    return index_instance

# Pydantic моделі на межі
class SearchResponseItem(BaseModel):
    doc_id: int
    name: str
    score: float
    snippet: str

class StatsResponse(BaseModel):
    num_docs: int
    vocab_size: int
    avg_doc_length: float

@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as e:
        logger.exception(f"[{request_id}] Неочікувана помилка: {e}")
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"detail": "Внутрішня помилка сервера", "request_id": request_id}
        )

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check(idx: Index | None = Depends(get_index)):
    if idx is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Індекс не завантажено"
        )
    return {"status": "ok", "docs": idx.num_docs}

@app.get("/stats", response_model=StatsResponse)
def get_stats(idx: Index = Depends(get_index)):
    return StatsResponse(
        num_docs=idx.num_docs,
        vocab_size=len(idx),
        avg_doc_length=idx.avg_doc_length
    )

@app.get("/search", response_model=list[SearchResponseItem])
async def api_search(
    q: str = Query(..., min_length=1),
    k: int = Query(5, ge=1, le=50),
    scorer: Literal["bm25", "tfidf"] = "bm25",
    idx: Index = Depends(get_index)
):
    scoring_alg = BM25() if scorer == "bm25" else TfIdf()
    results: list[SearchResult] = search(q, idx, scoring_alg, settings.corpus_path, top_k=k)
    return [
        SearchResponseItem(
            doc_id=r.doc_id,
            name=r.name,
            score=r.score,
            snippet=r.snippet
        ) for r in results
    ]

@app.get("/docs/{doc_id}")
def get_document(doc_id: int, idx: Index = Depends(get_index)):
    if doc_id not in idx._doc_meta:
        raise HTTPException(status_code=404, detail="Документ не знайдено")
    meta = idx._doc_meta[doc_id]
    return {"doc_id": meta.doc_id, "name": meta.name, "length": meta.length}

@app.get("/", response_class=HTMLResponse)
async def web_index(request: Request, q: str = "", scorer: Literal["bm25", "tfidf"] = "bm25"):
    results = []
    if q and index_instance:
        scoring_alg = BM25() if scorer == "bm25" else TfIdf()
        results = search(q, index_instance, scoring_alg, settings.corpus_path, top_k=10)
    # Виправлений виклик TemplateResponse для сучасних версій Starlette
    return templates.TemplateResponse(
        request,
        "index.html",
        {"request": request, "q": q, "results": results, "scorer": scorer}
    )