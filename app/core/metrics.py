from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
import logging
from .logging import get_logger
from .config import settings

logger = get_logger("metrics")


class Metrics:
    def __init__(self):
        self.meter = metrics.get_meter(settings.OTEL_SERVICE_NAME)

        # HTTP metrics
        self.http_request_counter = self.meter.create_counter(
            name=settings.get_metric_name("http_requests_total"),
            description=settings.get_metric_description("http_requests_total"),
            unit=settings.OTEL_DEFAULT_METRIC_UNIT,
        )

        self.http_error_counter = self.meter.create_counter(
            name=settings.get_metric_name("http_errors_total"),
            description=settings.get_metric_description("http_errors_total"),
            unit=settings.OTEL_DEFAULT_METRIC_UNIT,
        )

        self.request_latency = self.meter.create_histogram(
            name=settings.get_metric_name("http_request_duration_ms"),
            description=settings.get_metric_description("http_request_duration_ms"),
            unit="ms",
        )

        # Business metrics
        self.cart_items_gauge = self.meter.create_up_down_counter(
            name=settings.get_metric_name("cart_items_total"),
            description=settings.get_metric_description("cart_items_total"),
            unit=settings.OTEL_DEFAULT_METRIC_UNIT,
        )

        self.order_total_counter = self.meter.create_counter(
            name=settings.get_metric_name("order_total_amount"),
            description=settings.get_metric_description("order_total_amount"),
            unit="usd",
        )

        self.active_users_gauge = self.meter.create_up_down_counter(
            name=settings.get_metric_name("active_users"),
            description=settings.get_metric_description("active_users"),
            unit=settings.OTEL_DEFAULT_METRIC_UNIT,
        )

    def track_request(
        self, method: str, path: str, status_code: int, duration_ms: float
    ):
        """Track HTTP request metrics"""
        try:
            attributes = {
                "method": method,
                "path": path,
                "status_code": str(status_code),
            }

            self.http_request_counter.add(1, attributes)
            self.request_latency.record(duration_ms, attributes)

            if status_code >= 400:
                self.http_error_counter.add(1, attributes)

            logger.debug(
                f"Tracked request: {method} {path} {status_code} {duration_ms}ms"
            )
        except Exception as e:
            logger.error(f"Failed to track request metrics: {str(e)}")

    def track_cart_update(self, user_id: int, change: int):
        """Track cart item changes"""
        try:
            self.cart_items_gauge.add(change, {"user_id": str(user_id)})
            logger.debug(f"Tracked cart update: user={user_id} change={change}")
        except Exception as e:
            logger.error(f"Failed to track cart metrics: {str(e)}")

    def track_order(self, user_id: int, amount: float):
        """Track order placement"""
        try:
            self.order_total_counter.add(amount, {"user_id": str(user_id)})
            logger.debug(f"Tracked order: user={user_id} amount=${amount:.2f}")
        except Exception as e:
            logger.error(f"Failed to track order metrics: {str(e)}")

    def track_user_activity(self, user_id: int, active: bool = True):
        """Track user activity"""
        try:
            self.active_users_gauge.add(1 if active else -1, {"user_id": str(user_id)})
            logger.debug(f"Tracked user activity: user={user_id} active={active}")
        except Exception as e:
            logger.error(f"Failed to track user activity: {str(e)}")


def setup_metrics():
    """Initialize OpenTelemetry metrics"""
    logger.info("Setting up OpenTelemetry metrics...")

    if (
        not settings.OTEL_EXPORTER_OTLP_ENDPOINT
        or not settings.OTEL_EXPORTER_OTLP_HEADERS
    ):
        raise ValueError(
            "OTEL_EXPORTER_OTLP_ENDPOINT and OTEL_EXPORTER_OTLP_HEADERS must be set"
        )

    # Configure exporter
    exporter = OTLPMetricExporter(
        endpoint=settings.get_formatted_endpoint(),
        headers=settings.otel_headers_dict,
        timeout=settings.OTEL_METRIC_EXPORT_TIMEOUT,
    )

    # Configure reader
    reader = PeriodicExportingMetricReader(
        exporter, export_interval_millis=settings.OTEL_METRIC_EXPORT_INTERVAL_MS
    )

    # Configure provider
    provider = MeterProvider(
        metric_readers=[reader],
        resource=Resource.create(settings.otel_resource_attributes),
    )

    metrics.set_meter_provider(provider)
    logger.info("Metrics setup complete")

    return Metrics()


# Global metrics instance
metrics_client = None


def get_metrics():
    """Get the global metrics instance"""
    global metrics_client
    if metrics_client is None:
        metrics_client = setup_metrics()
    return metrics_client
