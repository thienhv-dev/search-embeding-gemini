from datetime import timedelta
from typing import Optional

from minio import Minio
from minio.error import S3Error

from ..config import get_settings


def get_minio_client() -> Minio:
    settings = get_settings()
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


def ensure_bucket_exists(client: Minio, bucket: str) -> None:
    try:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
    except S3Error as exc:
        if exc.code != "BucketAlreadyOwnedByYou":
            raise


def generate_presigned_upload(
    object_name: str,
    *,
    expires: Optional[int] = None,
) -> str:
    settings = get_settings()
    client = get_minio_client()
    ensure_bucket_exists(client, settings.minio_bucket)
    return client.presigned_put_object(
        settings.minio_bucket,
        object_name,
        expires=timedelta(seconds=expires or 3600),
    )

