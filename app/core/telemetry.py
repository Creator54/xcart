from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
import os
import logging
from .logging import get_logger
import grpc

logger = get_logger("telemetry")

# Enable debug logging for OpenTelemetry and gRPC
logging.getLogger('opentelemetry').setLevel(logging.DEBUG)
logging.getLogger('grpc').setLevel(logging.DEBUG)

class DebugMetricReader(PeriodicExportingMetricReader):
    def _export(self, metrics_data):
        try:
            logger.info(f"Starting metrics export to SigNoz...")
            logger.debug(f"Metrics data: {metrics_data}")
            result = super()._export(metrics_data)
            logger.info("Metrics exported successfully!")
            return result
        except Exception as e:
            logger.error(f"Failed to export metrics: {str(e)}", exc_info=True)
            raise

# Create metrics
meter = metrics.get_meter("xcart")  # Changed to lowercase to match service name

# HTTP metrics
http_request_counter = meter.create_counter(
    name="http_requests_total",
    description="Total number of HTTP requests",
    unit="1"
)

http_error_counter = meter.create_counter(
    name="http_errors_total",
    description="Total number of HTTP errors",
    unit="1"
)

request_latency = meter.create_histogram(
    name="http_request_duration_ms",
    description="HTTP request latency in milliseconds",
    unit="ms"
)

# Business metrics
cart_items_gauge = meter.create_up_down_counter(
    name="cart_items_total",
    description="Total number of items in user carts",
    unit="1"
)

order_total_counter = meter.create_counter(
    name="order_total_amount",
    description="Total amount of orders placed",
    unit="usd"
)

active_users_gauge = meter.create_up_down_counter(
    name="active_users",
    description="Number of active users",
    unit="1"
)

def setup_telemetry():
    """Initialize OpenTelemetry with SigNoz configuration"""
    logger.info("Setting up OpenTelemetry...")
    
    # Get configuration from environment
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    headers = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "").strip()

    logger.info(f"OTLP Endpoint: {endpoint}")
    logger.debug(f"OTLP Headers: {headers}")

    if not endpoint or not headers:
        logger.error("OpenTelemetry configuration missing!")
        raise ValueError(
            "OpenTelemetry configuration missing. Please set OTEL_EXPORTER_OTLP_ENDPOINT "
            "and OTEL_EXPORTER_OTLP_HEADERS environment variables."
        )

    try:
        # Parse headers
        logger.info("Parsing headers...")
        header_dict = {}
        if headers:
            for header in headers.split(","):
                if "=" in header:
                    key, value = header.split("=", 1)
                    header_dict[key.strip()] = value.strip()
        logger.debug(f"Parsed headers: {header_dict}")

        # Configure OTLP exporter
        logger.info("Configuring OTLP exporter...")
        
        # Format endpoint for gRPC
        if endpoint.startswith(("http://", "https://")):
            endpoint = endpoint.split("://")[1]
        if not endpoint.endswith(":443"):
            endpoint = f"{endpoint}:443"
            
        logger.info(f"Using gRPC endpoint: {endpoint}")
        
        # Create exporter
        exporter = OTLPMetricExporter(
            endpoint=f"https://{endpoint}",
            headers=header_dict,
            timeout=30,  # Increased timeout for debugging
            insecure=False  # Use TLS
        )
        logger.info("OTLP exporter configured successfully")

        # Configure metric reader with debug wrapper
        logger.info("Configuring metric reader...")
        reader = DebugMetricReader(
            exporter,
            export_interval_millis=5000  # Export every 5 seconds
        )
        logger.info("Metric reader configured with 5s export interval")

        # Configure resource attributes
        env = os.getenv("DEPLOYMENT_ENV", "development")
        logger.info(f"Configuring resource for environment: {env}")
        resource = Resource.create({
            SERVICE_NAME: "xcart",
            "deployment.environment": env,
            "service.version": "1.0.0",
            "telemetry.sdk.name": "opentelemetry",
            "telemetry.sdk.language": "python"
        })

        # Initialize meter provider
        logger.info("Initializing meter provider...")
        provider = MeterProvider(
            metric_readers=[reader],
            resource=resource
        )
        metrics.set_meter_provider(provider)
        logger.info("OpenTelemetry setup completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to setup OpenTelemetry: {str(e)}", exc_info=True)
        raise

def track_cart_items(user_id: int, change: int):
    """Track changes in cart items"""
    try:
        cart_items_gauge.add(change, {
            "user_id": str(user_id)
        })
        logger.info(f"Tracked cart items change: user={user_id}, change={change}")
    except Exception as e:
        logger.error(f"Failed to track cart items: {str(e)}")

def track_order_total(user_id: int, amount: float):
    """Track order amounts"""
    try:
        order_total_counter.add(amount, {
            "user_id": str(user_id)
        })
        logger.info(f"Tracked order total: user={user_id}, amount=${amount:.2f}")
    except Exception as e:
        logger.error(f"Failed to track order total: {str(e)}")

def track_request(method: str, path: str):
    """Track HTTP request"""
    try:
        http_request_counter.add(1, {
            "method": method,
            "path": path
        })
        logger.info(f"Tracked HTTP request: {method} {path}")
    except Exception as e:
        logger.error(f"Failed to track request: {str(e)}")

def track_user_activity(user_id: int, active: bool = True):
    """Track user activity"""
    try:
        active_users_gauge.add(1 if active else -1, {
            "user_id": str(user_id)
        })
        logger.info(f"Tracked user activity: user={user_id}, active={active}")
    except Exception as e:
        logger.error(f"Failed to track user activity: {str(e)}") 