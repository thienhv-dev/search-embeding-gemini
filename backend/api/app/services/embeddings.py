from __future__ import annotations

import logging
from functools import lru_cache
from typing import List

from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_client() -> genai.Client:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    return genai.Client(api_key=settings.gemini_api_key)


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

