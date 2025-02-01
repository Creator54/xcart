from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from time import time
from .config import settings
from .logging import get_logger

logger = get_logger("telemetry")

class Telemetry:
    """Unified telemetry management."""
    
    def __init__(self, meter):
        """Initialize telemetry with OpenTelemetry meter."""
        self.meter = meter
        
        # HTTP metrics
        self.http_requests = self.meter.create_counter(
            name=f"{settings.OTEL_SERVICE_NAME}_http_requests",
            description="Total HTTP requests",
            unit="1"
        )
        
        self.request_latency = self.meter.create_histogram(
            name=f"{settings.OTEL_SERVICE_NAME}_http_latency",
            description="HTTP request duration",
            unit="ms"
        )
        
        # Business metrics
        self.cart_items = self.meter.create_up_down_counter(
            name=f"{settings.OTEL_SERVICE_NAME}_cart_items",
            description="Total items in cart",
            unit="1"
        )
        
        self.order_total = self.meter.create_counter(
            name=f"{settings.OTEL_SERVICE_NAME}_order_total",
            description="Total order amount",
            unit="usd"
        )
        
        self.active_users = self.meter.create_up_down_counter(
            name=f"{settings.OTEL_SERVICE_NAME}_active_users",
            description="Total active users",
            unit="1"
        )

    def track_request(self, method: str, path: str, status_code: int, duration_ms: float):
        """Track HTTP request metrics."""
        attributes = {
            "method": method,
            "path": path,
            "status_code": str(status_code),
        }
        self.http_requests.add(1, attributes)
        self.request_latency.record(duration_ms, attributes)

    def track_cart_update(self, user_id: int, change: int):
        """Track cart item changes."""
        self.cart_items.add(change, {"user_id": str(user_id)})

    def track_order(self, user_id: int, amount: float):
        """Track order placement."""
        self.order_total.add(amount, {"user_id": str(user_id)})

    def track_user_activity(self, user_id: int, active: bool = True):
        """Track user activity."""
        self.active_users.add(1 if active else -1, {"user_id": str(user_id)})


class TelemetryMiddleware(BaseHTTPMiddleware):
    """Middleware for request telemetry."""
    
    async def dispatch(self, request: Request, call_next):
        if not settings.OTEL_ENABLED:
            return await call_next(request)
            
        start_time = time()
        response = await call_next(request)
        
        if telemetry := get_telemetry():
            telemetry.track_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=(time() - start_time) * 1000,
            )
            
        return response


# Global telemetry instance
_telemetry = None


def setup_telemetry(app: FastAPI = None) -> None:
    """Initialize OpenTelemetry with unified configuration."""
    if not settings.OTEL_ENABLED:
        logger.info("OpenTelemetry is disabled")
        return

    if not settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        logger.warning("OpenTelemetry disabled: OTEL_EXPORTER_OTLP_ENDPOINT not set")
        return

    try:
        global _telemetry
        
        # Common configuration
        endpoint = settings.get_formatted_endpoint()
        is_local = "localhost" in endpoint
        exporter_args = {
            "endpoint": endpoint,
            "timeout": settings.OTEL_METRIC_EXPORT_TIMEOUT,
            **({"insecure": True} if is_local else {"headers": settings.otel_headers_dict})
        }
        
        # Common resource
        resource = Resource.create(settings.otel_resource_attributes)

        # Setup metrics
        metrics.set_meter_provider(MeterProvider(
            metric_readers=[PeriodicExportingMetricReader(
                OTLPMetricExporter(**exporter_args),
                export_interval_millis=settings.OTEL_METRIC_EXPORT_INTERVAL_MS
            )],
            resource=resource
        ))
        _telemetry = Telemetry(metrics.get_meter(settings.OTEL_SERVICE_NAME))
        
        # Setup tracing if app provided
        if app:
            tracer = TracerProvider(resource=resource)
            trace.set_tracer_provider(tracer)
            tracer.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(**exporter_args)))
            FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer)
            
        logger.info("OpenTelemetry initialized successfully")
            
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}")
        if "Overriding of current MeterProvider is not allowed" in str(e):
            _telemetry = Telemetry(metrics.get_meter(settings.OTEL_SERVICE_NAME))


def get_telemetry():
    """Get the global telemetry instance."""
    return _telemetry


# Convenience functions for business metrics
def track_cart_items(user_id: int, change: int):
    """Track changes in cart items."""
    if settings.OTEL_ENABLED and (telemetry := get_telemetry()):
        telemetry.track_cart_update(user_id, change)

def track_order_total(user_id: int, amount: float):
    """Track order amounts."""
    if settings.OTEL_ENABLED and (telemetry := get_telemetry()):
        telemetry.track_order(user_id, amount)

def track_user_activity(user_id: int, active: bool = True):
    """Track user activity."""
    if settings.OTEL_ENABLED and (telemetry := get_telemetry()):
        telemetry.track_user_activity(user_id, active) 