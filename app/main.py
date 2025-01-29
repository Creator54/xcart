from fastapi import FastAPI
from app.core.database import engine, SessionLocal
from app.models import models
from app.routers import auth, products, cart, orders

models.Base.metadata.create_all(bind=engine)

def init_db():
    db = SessionLocal()
    if not db.query(models.Product).first():
        products = [
            {"name": "Gaming Laptop", "price": 999.99},
            {"name": "Wireless Mouse", "price": 29.99},
            {"name": "Mechanical Keyboard", "price": 89.99},
            {"name": "27-inch Monitor", "price": 299.99},
            {"name": "Noise-Canceling Headphones", "price": 199.99},
            {"name": "Webcam HD", "price": 59.99},
            {"name": "USB-C Hub", "price": 39.99},
            {"name": "External SSD 1TB", "price": 149.99},
            {"name": "Gaming Mouse Pad", "price": 19.99},
            {"name": "Laptop Stand", "price": 24.99}
        ]
        db.bulk_save_objects([models.Product(**p) for p in products])
        db.commit()
    db.close()

init_db()

app = FastAPI(
    title="XCart",
    description="A minimal e-commerce API with user authentication, cart and order management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(cart.router, prefix="/cart", tags=["cart"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
