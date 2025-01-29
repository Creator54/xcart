from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models import models
from app.schemas import schemas
from app.routers.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=schemas.Order)
def place_order(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart_items = current_user.cart_items
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    order = models.Order(
        user_id=current_user.id,
        total_amount=sum(item.quantity * item.product.price for item in cart_items)
    )
    db.add(order)
    
    # Clear cart items
    db.query(models.CartItem).filter(
        models.CartItem.user_id == current_user.id
    ).delete()
    
    db.commit()
    db.refresh(order)
    return order

@router.get("/", response_model=List[schemas.Order])
def get_orders(current_user: models.User = Depends(get_current_user)):
    return current_user.orders 