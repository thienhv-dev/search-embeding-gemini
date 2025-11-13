import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import EmbeddingJob, JobOperation, JobStatus


def enqueue_job(
    db: Session,
    *,
    product_id: uuid.UUID,
    operation: JobOperation,
) -> EmbeddingJob:
    """Create or update an embedding job for the given product."""
    existing = db.execute(
        select(EmbeddingJob).where(
            EmbeddingJob.product_id == product_id,
            EmbeddingJob.status.in_([JobStatus.PENDING, JobStatus.PROCESSING]),
        )
    ).scalar_one_or_none()

    if existing:
        existing.operation = operation
        existing.status = JobStatus.PENDING
        existing.error = None
        return existing

    job = EmbeddingJob(
        product_id=product_id,
        operation=operation,
        status=JobStatus.PENDING,
    )
    db.add(job)
    return job

