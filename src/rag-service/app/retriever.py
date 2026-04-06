# src/rag-service/app/retriever.py
# 역할: 벡터 유사도 검색 — sentence_transformers 임베딩 + Qdrant
# 관련 챕터: Chapter 2, 6

import logging
from qdrant_client import AsyncQdrantClient
from sentence_transformers import SentenceTransformer

from app.config import settings

logger = logging.getLogger(__name__)

_embedder: SentenceTransformer | None = None
_qdrant: AsyncQdrantClient | None = None


def get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        logger.info("loading embedding model: %s", settings.embedding_model)
        _embedder = SentenceTransformer(settings.embedding_model)
    return _embedder


def get_qdrant() -> AsyncQdrantClient:
    global _qdrant
    if _qdrant is None:
        _qdrant = AsyncQdrantClient(url=settings.qdrant_url)
    return _qdrant


class RAGRetriever:

    async def search(self, query: str, top_k: int = None) -> list[dict]:
        top_k = top_k or settings.top_k_default
        embedder = get_embedder()
        qdrant   = get_qdrant()

        # 쿼리 임베딩 생성
        query_vector = embedder.encode(query).tolist()

        # Qdrant 유사도 검색
        results = await qdrant.search(
            collection_name=settings.qdrant_collection,
            query_vector=query_vector,
            limit=top_k,
            with_payload=True,
        )

        return [
            {
                "content": r.payload.get("content", ""),
                "source":  r.payload.get("source", ""),
                "score":   r.score,
            }
            for r in results
        ]
