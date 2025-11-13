from __future__ import annotations

import logging
from typing import List

from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import get_settings

logger = logging.getLogger(__name__)

_client: genai.Client | None = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured for embedding worker.")
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, max=30))
def embed_texts(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    client = get_client()
    settings = get_settings()
    response = client.models.embed_content(
        model=settings.embedding_model,
        contents=texts,
    )
    embeddings = response.embeddings or []
    return [embedding.values or [] for embedding in embeddings]

