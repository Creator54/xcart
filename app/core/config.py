from pydantic_settings import BaseSettings
from typing import Dict, Any, List
import os


class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "XCart Backend"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "XCart Backend"
    APP_DOCS_URL: str = "/docs"
    APP_REDOC_URL: str | None = None
    APP_ROOT_PATH: str = ""
    DEBUG: bool = True

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    WORKERS: int = 1

    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # Authentication settings
    SECRET_KEY: str = "don't tell anyone"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    PASSWORD_BCRYPT_ROUNDS: int = 12
    OAUTH2_TOKEN_URL: str = "auth/login"

    # Database settings
    DATABASE_URL: str = "sqlite:///./xcart.db"
    DATABASE_CONNECT_ARGS: Dict[str, Any] = {"check_same_thread": False}
    DATABASE_ECHO: bool = False

    # Sample data settings
    INITIALIZE_DB: bool = True
    SAMPLE_PRODUCTS: List[Dict[str, Any]] = [
        {"name": "Gaming Laptop", "price": 999.99},
        {"name": "Wireless Mouse", "price": 29.99},
        {"name": "Mechanical Keyboard", "price": 89.99},
        {"name": "27-inch Monitor", "price": 299.99},
        {"name": "Noise-Canceling Headphones", "price": 199.99},
        {"name": "Webcam HD", "price": 59.99},
        {"name": "USB-C Hub", "price": 39.99},
        {"name": "External SSD 1TB", "price": 149.99},
        {"name": "Gaming Mouse Pad", "price": 19.99},
        {"name": "Laptop Stand", "price": 24.99},
    ]

    # Business logic settings
    MIN_ORDER_AMOUNT: float = 24.99

    # OpenTelemetry settings
    OTEL_ENABLED: bool = True
    OTEL_SERVICE_NAME: str = os.getenv("OTEL_RESOURCE_ATTRIBUTES").split("=")[1]
    OTEL_EXPORTER_OTLP_ENDPOINT: str = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    OTEL_EXPORTER_OTLP_HEADERS: str = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "").strip()
    OTEL_METRIC_EXPORT_INTERVAL_MS: int = 5000  # Increased to 5 seconds
    OTEL_METRIC_EXPORT_TIMEOUT: int = 10  # Increased timeout
    DEPLOYMENT_ENV: str = os.getenv("DEPLOYMENT_ENV", "development")

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    LOG_TO_FILE: bool = False
    LOG_FILE_PATH: str = "logs/xcart.log"
    LOG_FILE_MAX_BYTES: int = 10_485_760  # 10MB
    LOG_FILE_BACKUP_COUNT: int = 5

    @property
    def otel_headers_dict(self) -> Dict[str, str]:
        """Parse OTLP headers into a dictionary."""
        headers = {}
        if self.OTEL_EXPORTER_OTLP_HEADERS:
            for header in self.OTEL_EXPORTER_OTLP_HEADERS.split(","):
                if "=" in header:
                    key, value = header.split("=", 1)
                    headers[key.strip()] = value.strip()
        return headers

    @property
    def otel_resource_attributes(self) -> Dict[str, Any]:
        """Get OpenTelemetry resource attributes."""
        return {
            "service.name": self.OTEL_SERVICE_NAME,
            "service.version": self.APP_VERSION,
            "deployment.environment": self.DEPLOYMENT_ENV,
        }

    def get_formatted_endpoint(self) -> str:
        """Format the OTLP endpoint for gRPC."""
        endpoint = self.OTEL_EXPORTER_OTLP_ENDPOINT
        if endpoint.startswith(("http://", "https://")):
            endpoint = endpoint.split("://")[1]
        return endpoint

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()
