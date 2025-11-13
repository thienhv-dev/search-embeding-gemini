from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from opensearchpy import OpenSearch

from ..config import get_settings
from ..schemas import SearchHit, SearchResponse
from ..services.embeddings import embed_texts
from ..services.search_index import get_opensearch_client

router = APIRouter(prefix="/search", tags=["search"])


def get_client() -> OpenSearch:
    return get_opensearch_client()


@router.get("/", response_model=SearchResponse)
def search_products(
    q: str = Query(..., min_length=1, description="Search query"),
    k: int = Query(5, ge=1, le=50, description="Number of results"),
    client: OpenSearch = Depends(get_client),
) -> SearchResponse:
    settings = get_settings()

    embeddings = embed_texts([q])
    if not embeddings:
        raise HTTPException(status_code=500, detail="Failed to compute query embedding.")

    vector = embeddings[0]
    try:
        if not client.indices.exists(index=settings.opensearch_index):
            return SearchResponse(query=q, hits=[])

        response = client.search(
            index=settings.opensearch_index,
            body={
                "size": k,
                "query": {
                    "knn": {
                        "vector": {
                            "vector": vector,
                            "k": k,
                        }
                    }
                },
            },
        )
    except Exception as exc:  # pragma: no cover - network errors
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    hits: List[SearchHit] = []
    for hit in response.get("hits", {}).get("hits", []):
        source = hit.get("_source", {})
        hits.append(
            SearchHit(
                product_id=source.get("product_id"),
                chunk_id=source.get("chunk_id"),
                score=hit.get("_score", 0.0),
                chunk_text=source.get("chunk_text", ""),
                name=source.get("name", ""),
                images=source.get("images", []),
            )
        )

    return SearchResponse(query=q, hits=hits)

