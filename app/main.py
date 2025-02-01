from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, SessionLocal
from app.core.logging import setup_logging, get_logger
from app.core.telemetry import setup_telemetry, TelemetryMiddleware
from app.core.config import settings
from app.models import models
from app.routers import auth, products, cart, orders

# Setup logging
setup_logging()
logger = get_logger("app")

# Create database tables
logger.info("Creating database tables...")
models.Base.metadata.create_all(bind=engine)


def init_db():
    """Initialize database with sample products if enabled"""
    if not settings.INITIALIZE_DB:
        logger.info("Database initialization skipped (INITIALIZE_DB=False)")
        return

    logger.info("Initializing database with sample products...")
    db = SessionLocal()
    if not db.query(models.Product).first():
        for product in settings.SAMPLE_PRODUCTS:
            db.add(models.Product(
                name=product["name"],
                price=product["price"]
            ))
        db.commit()
        logger.info("Sample products created successfully")
    db.close()


# Initialize database
init_db()


def create_app() -> FastAPI:
    logger.info("Starting XCart application...")

    # Create FastAPI app
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        docs_url=settings.APP_DOCS_URL,
        redoc_url=settings.APP_REDOC_URL,
        root_path=settings.APP_ROOT_PATH,
        debug=settings.DEBUG,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

    # Add telemetry middleware
    app.add_middleware(TelemetryMiddleware)

    # Include routers
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(products.router, prefix="/products", tags=["products"])
    app.include_router(cart.router, prefix="/cart", tags=["cart"])
    app.include_router(orders.router, prefix="/orders", tags=["orders"])

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app


app = create_app()

# Setup OpenTelemetry
setup_telemetry(app)

logger.info("Application startup complete")
