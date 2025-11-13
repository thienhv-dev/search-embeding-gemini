from __future__ import annotations

import logging
from typing import Any, Dict, List

from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk

from ..config import get_settings

logger = logging.getLogger(__name__)


def get_opensearch_client() -> OpenSearch:
    settings = get_settings()
    return OpenSearch(
        settings.opensearch_hosts,
        http_compress=True,
        timeout=30,
        retry_on_timeout=True,
        max_retries=3,
        use_ssl=True,
        verify_certs=False,
        ssl_show_warn=False,
        http_auth=(settings.opensearch_username, settings.opensearch_password),
    )


def ensure_index(client: OpenSearch, *, dimension: int) -> None:
    settings = get_settings()
    index_name = settings.opensearch_index
    if client.indices.exists(index=index_name):
        return

    body = {
        "settings": {
            "index": {
                "knn": True,
                "knn.algo_param.ef_search": 100,
            }
        },
        "mappings": {
            "properties": {
                "product_id": {"type": "keyword"},
                "chunk_id": {"type": "keyword"},
                "name": {"type": "text"},
                "images": {"type": "keyword"},
                "chunk_text": {"type": "text"},
                "vector": {
                    "type": "knn_vector",
                    "dimension": dimension,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "lucene",
                    },
                },
            }
        },
    }
    client.indices.create(index=index_name, body=body)
    logger.info("Created OpenSearch index '%s' with dimension %s", index_name, dimension)


def delete_product_vectors(client: OpenSearch, *, product_id: str) -> None:
    settings = get_settings()
    index_name = settings.opensearch_index
    if not client.indices.exists(index=index_name):
        return
    client.delete_by_query(
        index=index_name,
        body={"query": {"term": {"product_id": product_id}}},
        refresh=True,
    )


def index_product_vectors(
    client: OpenSearch,
    *,
    product_id: str,
    name: str,
    images: List[str] | None,
    chunks: List[Dict[str, Any]],
) -> None:
    settings = get_settings()
    index_name = settings.opensearch_index
    actions = []
    for chunk in chunks:
        actions.append(
            {
                "_op_type": "index",
                "_index": index_name,
                "_id": chunk["chunk_id"],
                "_source": {
                    "product_id": product_id,
                    "chunk_id": chunk["chunk_id"],
                    "chunk_text": chunk["text"],
                    "vector": chunk["embedding"],
                    "name": name,
                    "images": images or [],
                },
            }
        )
    if actions:
        bulk(client, actions, refresh=True)

