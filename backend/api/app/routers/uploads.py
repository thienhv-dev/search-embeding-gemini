import uuid

from fastapi import APIRouter, HTTPException, Query

from ..services.storage import generate_presigned_upload

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.get("/presign")
def get_presigned_url(
    filename: str = Query(..., description="Original filename"),
) -> dict[str, str]:
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    object_name = f"{uuid.uuid4()}-{filename}"
    url = generate_presigned_upload(object_name)
    return {"object_name": object_name, "url": url}

