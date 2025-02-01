from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.telemetry import track_order_total
from app.core.config import settings
from app.models import models
from app.schemas import schemas
from app.routers.auth import get_current_user

router = APIRouter()
logger = get_logger("orders")


@router.post("/", response_model=schemas.Order)
def place_order(
    current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
):
    cart_items = current_user.cart_items
    if not cart_items:
        logger.warning(
            f"User {current_user.email} tried to place order with empty cart"
        )
        raise HTTPException(status_code=400, detail="Cart is empty")

    total_amount = sum(item.quantity * item.product.price for item in cart_items)

    # Validate minimum order amount
    if total_amount < settings.MIN_ORDER_AMOUNT:
        logger.warning(
            f"User {current_user.email} tried to place order below minimum amount (${total_amount:.2f})"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Order total must be at least ${settings.MIN_ORDER_AMOUNT:.2f}",
        )

    order = models.Order(user_id=current_user.id, total_amount=total_amount)
    db.add(order)

    # Clear cart items
    items_count = len(cart_items)
    db.query(models.CartItem).filter(
        models.CartItem.user_id == current_user.id
    ).delete()

    db.commit()
    db.refresh(order)

    # Track order metrics
    track_order_total(current_user.id, total_amount)

    logger.info(
        f"User {current_user.email} placed order #{order.id} with {items_count} items, total: ${total_amount:.2f}"
    )
    return order


@router.get("/", response_model=List[schemas.Order])
def get_orders(current_user: models.User = Depends(get_current_user)):
    logger.info(f"User {current_user.email} viewed their orders")
    return current_user.orders
