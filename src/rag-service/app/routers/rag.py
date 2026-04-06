# src/rag-service/app/routers/rag.py
# 역할: /rag/search 엔드포인트
# 관련 챕터: Chapter 6

from fastapi import APIRouter, HTTPException
from app.schemas.rag import SearchRequest, SearchResponse, SearchResult
from app.retriever import RAGRetriever

router = APIRouter(prefix="/rag")
_retriever = RAGRetriever()


@router.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest) -> SearchResponse:
    try:
        results = await _retriever.search(req.query, req.top_k)
        return SearchResponse(results=[SearchResult(**r) for r in results])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG 검색 실패: {e}")
