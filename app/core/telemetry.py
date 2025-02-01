from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
import os
import logging
from typing import Optional, Dict, Any
from .logging import get_logger
import grpc
from .config import settings

# Configure logging
logger = get_logger("telemetry")
logging.getLogger("opentelemetry").setLevel(getattr(logging, settings.OTEL_LOG_LEVEL))
logging.getLogger("grpc").setLevel(getattr(logging, settings.GRPC_LOG_LEVEL))


class MetricsState:
    """Global state for OpenTelemetry metrics"""
    def __init__(self):
        self.meter: Optional[metrics.Meter] = None
        self._metrics: Dict[str, Any] = {}

    def get_metric(self, name: str) -> Any:
        """Get a metric by name"""
        return self._metrics.get(name)

    def register_metric(self, name: str, metric: Any) -> None:
        """Register a new metric"""
        self._metrics[name] = metric


metrics_state = MetricsState()


class DebugMetricReader(PeriodicExportingMetricReader):
    """Custom metric reader with debug logging"""
    def _export(self, metrics_data):
        try:
            logger.info("Starting metrics export to SigNoz...")
            logger.debug(f"Metrics data: {metrics_data}")
            result = super()._export(metrics_data)
            logger.info("Metrics exported successfully!")
            return result
        except Exception as e:
            logger.error(f"Failed to export metrics: {str(e)}", exc_info=True)
            raise


def create_metric(meter: metrics.Meter, metric_type: str, name: str, description: str, unit: str) -> Any:
    """Helper function to create metrics with consistent naming"""
    metric_name = settings.get_metric_name(name)
    logger.debug(f"Creating {metric_type} metric: {metric_name}")
    
    if metric_type == "counter":
        return meter.create_counter(name=metric_name, description=description, unit=unit)
    elif metric_type == "up_down_counter":
        return meter.create_up_down_counter(name=metric_name, description=description, unit=unit)
    elif metric_type == "histogram":
        return meter.create_histogram(name=metric_name, description=description, unit=unit)
    else:
        raise ValueError(f"Unsupported metric type: {metric_type}")


def setup_telemetry():
    """Initialize OpenTelemetry with SigNoz configuration"""
    logger.info("Setting up OpenTelemetry...")

    logger.info(f"OTLP Endpoint: {settings.OTEL_EXPORTER_OTLP_ENDPOINT}")
    logger.debug(f"OTLP Headers: {settings.OTEL_EXPORTER_OTLP_HEADERS}")
    logger.info(f"Service Name: {settings.OTEL_SERVICE_NAME}")

    if not settings.OTEL_EXPORTER_OTLP_ENDPOINT or not settings.OTEL_EXPORTER_OTLP_HEADERS:
        logger.error("OpenTelemetry configuration missing!")
        raise ValueError(
            "OpenTelemetry configuration missing. Please set OTEL_EXPORTER_OTLP_ENDPOINT "
            "and OTEL_EXPORTER_OTLP_HEADERS environment variables."
        )

    try:
        # Parse headers
        logger.info("Parsing headers...")
        header_dict = settings.otel_headers_dict
        logger.debug(f"Parsed headers: {header_dict}")

        # Configure OTLP exporter
        logger.info("Configuring OTLP exporter...")
        endpoint = settings.get_formatted_endpoint()
        logger.info(f"Using gRPC endpoint: {endpoint}")

        # Create exporter
        exporter = OTLPMetricExporter(
            endpoint=endpoint,
            headers=header_dict,
            timeout=settings.OTEL_METRIC_EXPORT_TIMEOUT,
            insecure=not settings.OTEL_USE_TLS,
        )
        logger.info("OTLP exporter configured successfully")

        # Configure metric reader with debug wrapper
        logger.info("Configuring metric reader...")
        reader = DebugMetricReader(
            exporter, export_interval_millis=settings.OTEL_METRIC_EXPORT_INTERVAL_MS
        )
        logger.info(f"Metric reader configured with {settings.OTEL_METRIC_EXPORT_INTERVAL_MS}ms export interval")

        # Configure resource attributes
        logger.info(f"Configuring resource for environment: {settings.DEPLOYMENT_ENV}")
        resource = Resource.create(settings.otel_resource_attributes)

        # Initialize meter provider
        logger.info("Initializing meter provider...")
        provider = MeterProvider(metric_readers=[reader], resource=resource)
        metrics.set_meter_provider(provider)
        logger.info("OpenTelemetry setup completed successfully")

        # Create metrics
        metrics_state.meter = metrics.get_meter(settings.OTEL_SERVICE_NAME)

        # HTTP metrics
        metrics_state.register_metric(
            settings.METRIC_HTTP_REQUESTS,
            create_metric(
                metrics_state.meter,
                "counter",
                settings.METRIC_HTTP_REQUESTS,
                settings.METRIC_DESC_HTTP_REQUESTS,
                settings.METRIC_UNIT_DEFAULT,
            )
        )

        metrics_state.register_metric(
            settings.METRIC_HTTP_ERRORS,
            create_metric(
                metrics_state.meter,
                "counter",
                settings.METRIC_HTTP_ERRORS,
                settings.METRIC_DESC_HTTP_ERRORS,
                settings.METRIC_UNIT_DEFAULT,
            )
        )

        metrics_state.register_metric(
            settings.METRIC_REQUEST_LATENCY,
            create_metric(
                metrics_state.meter,
                "histogram",
                settings.METRIC_REQUEST_LATENCY,
                settings.METRIC_DESC_REQUEST_LATENCY,
                settings.METRIC_UNIT_MS,
            )
        )

        # Business metrics
        metrics_state.register_metric(
            settings.METRIC_CART_ITEMS,
            create_metric(
                metrics_state.meter,
                "up_down_counter",
                settings.METRIC_CART_ITEMS,
                settings.METRIC_DESC_CART_ITEMS,
                settings.METRIC_UNIT_DEFAULT,
            )
        )

        metrics_state.register_metric(
            settings.METRIC_ORDER_TOTAL,
            create_metric(
                metrics_state.meter,
                "counter",
                settings.METRIC_ORDER_TOTAL,
                settings.METRIC_DESC_ORDER_TOTAL,
                settings.METRIC_UNIT_USD,
            )
        )

        metrics_state.register_metric(
            settings.METRIC_ACTIVE_USERS,
            create_metric(
                metrics_state.meter,
                "up_down_counter",
                settings.METRIC_ACTIVE_USERS,
                settings.METRIC_DESC_ACTIVE_USERS,
                settings.METRIC_UNIT_DEFAULT,
            )
        )

    except Exception as e:
        logger.error(f"Failed to setup OpenTelemetry: {str(e)}", exc_info=True)
        raise


def track_cart_items(user_id: int, change: int):
    """Track changes in cart items"""
    try:
        metric = metrics_state.get_metric(settings.METRIC_CART_ITEMS)
        metric.add(change, {"user_id": str(user_id)})
        logger.info(f"Tracked cart items change: user={user_id}, change={change}")
    except Exception as e:
        logger.error(f"Failed to track cart items: {str(e)}")


def track_order_total(user_id: int, amount: float):
    """Track order amounts"""
    try:
        metric = metrics_state.get_metric(settings.METRIC_ORDER_TOTAL)
        metric.add(amount, {"user_id": str(user_id)})
        logger.info(f"Tracked order total: user={user_id}, amount=${amount:.2f}")
    except Exception as e:
        logger.error(f"Failed to track order total: {str(e)}")


def track_request(method: str, path: str):
    """Track HTTP request"""
    try:
        metric = metrics_state.get_metric(settings.METRIC_HTTP_REQUESTS)
        metric.add(1, {"method": method, "path": path})
        logger.info(f"Tracked HTTP request: {method} {path}")
    except Exception as e:
        logger.error(f"Failed to track request: {str(e)}")


def track_user_activity(user_id: int, active: bool = True):
    """Track user activity"""
    try:
        metric = metrics_state.get_metric(settings.METRIC_ACTIVE_USERS)
        metric.add(1 if active else -1, {"user_id": str(user_id)})
        logger.info(f"Tracked user activity: user={user_id}, active={active}")
    except Exception as e:
        logger.error(f"Failed to track user activity: {str(e)}")
