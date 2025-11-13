import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl

from .models import JobOperation, JobStatus


class ProductBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    images: Optional[List[HttpUrl]] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    images: Optional[List[HttpUrl] | List[str]] = None


class ProductResponse(ProductBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmbeddingJobResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    operation: JobOperation
    status: JobStatus
    error: Optional[str] = None
    attempts: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SearchHit(BaseModel):
    product_id: uuid.UUID
    score: float
    chunk_id: str
    chunk_text: str
    name: str
    images: List[str] | None = None


class SearchResponse(BaseModel):
    query: str
    hits: List[SearchHit]

