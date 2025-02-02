from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.telemetry import get_telemetry
from app.core.config import settings
from app.models import models
from app.schemas import schemas
from app.routers.auth import get_current_user

router = APIRouter()
logger = get_logger("cart")

@router.get("/", response_model=List[schemas.CartItem])
def view_cart(current_user: models.User = Depends(get_current_user)):
    logger.info(f"User {current_user.email} viewed their cart")
    return current_user.cart_items

@router.post("/add", response_model=schemas.CartItem)
def add_to_cart(
    item: schemas.CartItemCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if product exists
    product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
    if not product:
        logger.warning(f"User {current_user.email} tried to add non-existent product {item.product_id}")
        raise HTTPException(status_code=404, detail="Product not found")
    
    cart_item = models.CartItem(
        user_id=current_user.id,
        product_id=item.product_id,
        quantity=item.quantity
    )
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    
    logger.info(f"User {current_user.email} added {item.quantity} of product {product.name} to cart")
    return cart_item

@router.delete("/{item_id}")
def remove_from_cart(
    item_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart_item = db.query(models.CartItem).filter(
        models.CartItem.id == item_id,
        models.CartItem.user_id == current_user.id
    ).first()
    if not cart_item:
        logger.warning(f"User {current_user.email} tried to remove non-existent cart item {item_id}")
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    logger.info(f"User {current_user.email} removed {cart_item.quantity} of product {cart_item.product.name} from cart")
    
    db.delete(cart_item)
    db.commit()
    return {"message": "Item removed from cart"} 