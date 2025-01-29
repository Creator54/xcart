from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models import models
from app.schemas import schemas

router = APIRouter()

@router.get("/", response_model=List[schemas.Product])
def get_products(db: Session = Depends(get_db)):
    """
    Get all available products in the shop
    """
    return db.query(models.Product).all()

@router.get("/{product_id}", response_model=schemas.Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    Get a specific product by ID
    """
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product 