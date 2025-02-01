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
    MAX_CART_ITEMS: int = 10
    MAX_QUANTITY_PER_ITEM: int = 5

    # OpenTelemetry settings
    OTEL_EXPORTER_OTLP_ENDPOINT: str = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT", ""
    ).strip()
    OTEL_EXPORTER_OTLP_HEADERS: str = os.getenv(
        "OTEL_EXPORTER_OTLP_HEADERS", ""
    ).strip()
    OTEL_RESOURCE_ATTRIBUTES: str = os.getenv(
        "OTEL_RESOURCE_ATTRIBUTES", "service.name=xcart-v1"
    ).strip()
    DEPLOYMENT_ENV: str = os.getenv("DEPLOYMENT_ENV", "development")

    # OpenTelemetry configuration
    OTEL_SERVICE_NAME: str = (
        OTEL_RESOURCE_ATTRIBUTES.split("=")[1]
        if "=" in OTEL_RESOURCE_ATTRIBUTES
        else "xcart"
    )
    OTEL_METRIC_EXPORT_INTERVAL_MS: int = 5000
    OTEL_METRIC_EXPORT_TIMEOUT: int = 5
    OTEL_DEFAULT_METRIC_UNIT: str = "1"
    OTEL_SERVICE_VERSION: str = APP_VERSION
    OTEL_SDK_NAME: str = "opentelemetry"
    OTEL_SDK_LANGUAGE: str = "python"
    OTEL_USE_TLS: bool = True
    OTEL_GRPC_PORT: int = 443

    # OpenTelemetry metric names
    METRIC_HTTP_REQUESTS: str = "http_requests_total"
    METRIC_HTTP_ERRORS: str = "http_errors_total"
    METRIC_REQUEST_LATENCY: str = "http_request_duration_ms"
    METRIC_CART_ITEMS: str = "cart_items_total"
    METRIC_ORDER_TOTAL: str = "order_total_amount"
    METRIC_ACTIVE_USERS: str = "active_users"

    # OpenTelemetry metric descriptions
    METRIC_DESC_HTTP_REQUESTS: str = "Total number of HTTP requests"
    METRIC_DESC_HTTP_ERRORS: str = "Total number of HTTP errors"
    METRIC_DESC_REQUEST_LATENCY: str = "HTTP request latency in milliseconds"
    METRIC_DESC_CART_ITEMS: str = "Total number of items in user carts"
    METRIC_DESC_ORDER_TOTAL: str = "Total amount of orders placed"
    METRIC_DESC_ACTIVE_USERS: str = "Number of active users"

    # OpenTelemetry metric units
    METRIC_UNIT_DEFAULT: str = "1"
    METRIC_UNIT_MS: str = "ms"
    METRIC_UNIT_USD: str = "usd"

    # OpenTelemetry logging settings
    OTEL_LOG_LEVEL: str = "DEBUG"
    GRPC_LOG_LEVEL: str = "DEBUG"

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
        """Parse OTLP headers into a dictionary"""
        headers = {}
        if self.OTEL_EXPORTER_OTLP_HEADERS:
            for header in self.OTEL_EXPORTER_OTLP_HEADERS.split(","):
                if "=" in header:
                    key, value = header.split("=", 1)
                    headers[key.strip()] = value.strip()
        return headers

    @property
    def otel_resource_attributes(self) -> Dict[str, Any]:
        """Get OpenTelemetry resource attributes"""
        return {
            "service.name": self.OTEL_SERVICE_NAME,
            "deployment.environment": self.DEPLOYMENT_ENV,
            "service.version": self.APP_VERSION,
            "telemetry.sdk.name": "opentelemetry",
            "telemetry.sdk.language": "python",
        }

    def get_formatted_endpoint(self) -> str:
        """Format the OTLP endpoint for gRPC"""
        endpoint = self.OTEL_EXPORTER_OTLP_ENDPOINT
        if endpoint.startswith(("http://", "https://")):
            endpoint = endpoint.split("://")[1]
        if not endpoint.endswith(":443"):
            endpoint = f"{endpoint}:443"
        return f"https://{endpoint}"

    def get_metric_name(self, metric_name: str) -> str:
        """Get prefixed metric name with service name"""
        return f"{self.OTEL_SERVICE_NAME}_{metric_name}"
    
    def get_metric_description(self, metric_name: str) -> str:
        """Get metric description"""
        return f"{self.OTEL_SERVICE_NAME} {metric_name.replace('_', ' ').capitalize()}"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()
