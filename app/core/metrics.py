from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
import os
import logging
from .logging import get_logger

logger = get_logger("metrics")

class Metrics:
    def __init__(self):
        self.meter = metrics.get_meter("xcart")
        
        # HTTP metrics
        self.http_request_counter = self.meter.create_counter(
            name="http_requests_total",
            description="Total number of HTTP requests",
            unit="1"
        )
        
        self.http_error_counter = self.meter.create_counter(
            name="http_errors_total",
            description="Total number of HTTP errors",
            unit="1"
        )
        
        self.request_latency = self.meter.create_histogram(
            name="http_request_duration_ms",
            description="HTTP request latency in milliseconds",
            unit="ms"
        )
        
        # Business metrics
        self.cart_items_gauge = self.meter.create_up_down_counter(
            name="cart_items_total",
            description="Total number of items in user carts",
            unit="1"
        )
        
        self.order_total_counter = self.meter.create_counter(
            name="order_total_amount",
            description="Total amount of orders placed",
            unit="usd"
        )
        
        self.active_users_gauge = self.meter.create_up_down_counter(
            name="active_users",
            description="Number of active users",
            unit="1"
        )
    
    def track_request(self, method: str, path: str, status_code: int, duration_ms: float):
        """Track HTTP request metrics"""
        try:
            attributes = {
                "method": method,
                "path": path,
                "status_code": str(status_code)
            }
            
            self.http_request_counter.add(1, attributes)
            self.request_latency.record(duration_ms, attributes)
            
            if status_code >= 400:
                self.http_error_counter.add(1, attributes)
                
            logger.debug(f"Tracked request: {method} {path} {status_code} {duration_ms}ms")
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
    
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    headers = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "").strip()
    
    if not endpoint or not headers:
        raise ValueError("OTEL_EXPORTER_OTLP_ENDPOINT and OTEL_EXPORTER_OTLP_HEADERS must be set")
    
    # Parse headers
    header_dict = {}
    for header in headers.split(","):
        if "=" in header:
            key, value = header.split("=", 1)
            header_dict[key.strip()] = value.strip()
    
    # Configure exporter
    exporter = OTLPMetricExporter(
        endpoint=endpoint,
        headers=header_dict,
        timeout=30
    )
    
    # Configure reader
    reader = PeriodicExportingMetricReader(
        exporter,
        export_interval_millis=5000
    )
    
    # Configure provider
    provider = MeterProvider(
        metric_readers=[reader],
        resource=Resource.create({
            SERVICE_NAME: "xcart",
            "deployment.environment": os.getenv("DEPLOYMENT_ENV", "development"),
            "service.version": "1.0.0"
        })
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