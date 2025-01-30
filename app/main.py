from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, SessionLocal
from app.core.middleware import MetricsMiddleware
from app.core.logging import setup_logging, get_logger
from app.core.instrumentation import instrument_app
from app.core.metrics import setup_metrics
from app.models import models
from app.routers import auth, products, cart, orders

# Setup logging
setup_logging()
logger = get_logger("app")

# Create database tables
logger.info("Creating database tables...")
models.Base.metadata.create_all(bind=engine)

def init_db():
    logger.info("Initializing database with sample products...")
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
        logger.info("Sample products created successfully")
    db.close()

# Initialize database
init_db()

def create_app() -> FastAPI:
    # Initialize logging
    setup_logging()
    logger.info("Starting XCart application...")
    
    # Initialize metrics
    setup_metrics()
    logger.info("OpenTelemetry metrics initialized")
    
    # Create FastAPI app
    app = FastAPI(
        title="XCart API",
        description="E-commerce cart management API",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add metrics middleware
    app.add_middleware(MetricsMiddleware)
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    return app

app = create_app()

# Setup OpenTelemetry instrumentation
logger.info("Setting up OpenTelemetry instrumentation...")
instrument_app(app)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(cart.router, prefix="/cart", tags=["cart"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])

logger.info("Application startup complete")
