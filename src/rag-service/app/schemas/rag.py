# src/rag-service/app/schemas/rag.py
# 역할: RAG 요청/응답 스키마
# 관련 챕터: Chapter 6

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    content: str
    source: str
    score: float


class SearchResponse(BaseModel):
    results: list[SearchResult]
