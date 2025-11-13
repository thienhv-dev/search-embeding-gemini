import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..deps import get_db
from ..models import JobOperation, Product
from ..schemas import ProductCreate, ProductResponse, ProductUpdate
from ..services.jobs import enqueue_job

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=List[ProductResponse])
def list_products(db: Session = Depends(get_db)) -> List[Product]:
    return db.scalars(select(Product).order_by(Product.created_at.desc())).all()


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: uuid.UUID, db: Session = Depends(get_db)) -> Product:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)) -> Product:
    images = [str(url) for url in payload.images] if payload.images else None
    product = Product(
        name=payload.name,
        description=payload.description,
        images=images,
    )
    db.add(product)
    db.flush()  # ensure id is available
    enqueue_job(db, product_id=product.id, operation=JobOperation.UPSERT)
    db.commit()
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
) -> Product:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if payload.name is not None:
        product.name = payload.name
    if payload.description is not None:
        product.description = payload.description
    if payload.images is not None:
        product.images = [str(url) for url in payload.images]

    enqueue_job(db, product_id=product.id, operation=JobOperation.UPSERT)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    enqueue_job(db, product_id=product.id, operation=JobOperation.DELETE)
    db.delete(product)
    db.commit()

