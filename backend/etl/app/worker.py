from __future__ import annotations

import logging
import time
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .chunker import chunk_text
from .config import get_settings
from .database import engine, session_scope
from .embeddings import embed_texts
from .models import Base, EmbeddingJob, JobOperation, JobStatus, Product
from .search_index import delete_product, ensure_index, get_client, index_chunks

logger = logging.getLogger(__name__)


def fetch_next_job(db: Session) -> Optional[EmbeddingJob]:
    stmt = (
        select(EmbeddingJob)
        .where(EmbeddingJob.status == JobStatus.PENDING)
        .order_by(EmbeddingJob.created_at.asc())
        .with_for_update(skip_locked=True)
    )
    result = db.execute(stmt.limit(1)).scalars().first()
    return result


def process_job(db: Session, job: EmbeddingJob) -> None:
    settings = get_settings()
    job.status = JobStatus.PROCESSING
    job.attempts += 1
    job.error = None
    db.flush()

    search_client = get_client()

    logger.info("Processing job %s for product %s (%s)", job.id, job.product_id, job.operation.value)

    if job.operation == JobOperation.DELETE:
        delete_product(search_client, str(job.product_id))
        job.status = JobStatus.DONE
        db.delete(job)
        return

    product = db.get(Product, job.product_id)
    if not product:
        logger.warning("Product %s missing; marking job done.", job.product_id)
        job.status = JobStatus.DONE
        return

    base_text = "\n\n".join(
        filter(
            None,
            [
                product.name,
                product.description or "",
            ],
        )
    )
    chunks = chunk_text(
        base_text,
        chunk_size=settings.chunk_size,
        overlap=settings.chunk_overlap,
    )
    if not chunks:
        chunks = [product.name]

    embeddings = embed_texts(chunks)
    if not embeddings:
        logger.warning("No embeddings generated for product %s", product.id)
        job.status = JobStatus.DONE
        return

    dimension = len(embeddings[0])
    ensure_index(search_client, dimension)

    documents = []
    for idx, (chunk, vector) in enumerate(zip(chunks, embeddings)):
        documents.append(
            {
                "chunk_id": f"{job.product_id}-{idx}",
                "text": chunk,
                "embedding": vector,
            }
        )

    delete_product(search_client, str(product.id))
    index_chunks(
        search_client,
        product_id=str(product.id),
        name=product.name,
        images=product.images or [],
        chunks=documents,
    )
    job.status = JobStatus.DONE
    db.delete(job)


def run() -> None:
    settings = get_settings()
    Base.metadata.create_all(bind=engine)
    logger.info("Starting embedding worker loop")
    while True:
        with session_scope() as db:
            job = fetch_next_job(db)
            if not job:
                sleep_for = settings.poll_interval_seconds
            else:
                try:
                    process_job(db, job)
                    sleep_for = 0
                except Exception as exc:  # pragma: no cover - operational path
                    logger.exception("Failed processing job %s: %s", job.id, exc)
                    job.error = str(exc)
                    if job.attempts >= settings.max_attempts:
                        job.status = JobStatus.FAILED
                    else:
                        job.status = JobStatus.PENDING
                    db.flush()
                    sleep_for = settings.poll_interval_seconds
        if sleep_for:
            time.sleep(sleep_for)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()

