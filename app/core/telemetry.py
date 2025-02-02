"""OpenTelemetry instrumentation for application monitoring."""

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from time import time
from sqlalchemy import func, and_, Column, Integer, String, DateTime
from .config import settings
from .logging import get_logger
from datetime import datetime, timedelta

logger = get_logger("telemetry")

class Telemetry:
    """Real-time metrics tracking."""
    
    def __init__(self, meter):
        """Initialize telemetry with OpenTelemetry meter."""
        self.meter = meter
        
        # Observable Counter: Track error requests in real-time
        self.error_count = self.meter.create_observable_counter(
            name=f"{settings.OTEL_SERVICE_NAME}_http_errors_total",
            description="Total number of HTTP error responses",
            unit="1",
            callbacks=[self._observe_errors]
        )
        
        # Histogram: Track request latency
        self.request_latency = self.meter.create_histogram(
            name=f"{settings.OTEL_SERVICE_NAME}_http_request_duration_seconds",
            description="HTTP request latency in seconds",
            unit="s"
        )
        
        # Gauge: Track cart items in real-time
        self.cart_items = self.meter.create_observable_gauge(
            name=f"{settings.OTEL_SERVICE_NAME}_cart_items_total",
            description="Current number of items in cart",
            unit="1",
            callbacks=[self._observe_cart_items]
        )

        # Store errors in database
        from app.core.database import Base, engine
        class ErrorMetric(Base):
            __tablename__ = "error_metrics"
            id = Column(Integer, primary_key=True, index=True)
            method = Column(String)
            path = Column(String)
            status_code = Column(Integer)
            error_type = Column(String)
            timestamp = Column(DateTime(timezone=True), server_default=func.now())
        Base.metadata.create_all(bind=engine)
        self.ErrorMetric = ErrorMetric

    def _observe_errors(self, options):
        """Real-time observer for error metrics from database."""
        try:
            from app.core.database import SessionLocal
            
            db = SessionLocal()
            try:
                # Only count errors from the last minute
                one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
                
                # Get error counts grouped by method, path, status_code, and error_type
                results = db.query(
                    self.ErrorMetric.method,
                    self.ErrorMetric.path,
                    self.ErrorMetric.status_code,
                    self.ErrorMetric.error_type,
                    func.count().label('total')
                ).filter(
                    self.ErrorMetric.timestamp >= one_minute_ago
                ).group_by(
                    self.ErrorMetric.method,
                    self.ErrorMetric.path,
                    self.ErrorMetric.status_code,
                    self.ErrorMetric.error_type
                ).all()

                # Return measurements for each error type
                return [
                    metrics.Observation(
                        value=int(total),
                        attributes={
                            "method": method,
                            "path": path,
                            "status_code": str(status_code),
                            "error_type": error_type
                        }
                    )
                    for method, path, status_code, error_type, total in results
                ] or [metrics.Observation(value=0, attributes={
                    "method": "GET",
                    "path": "/",
                    "status_code": "200",
                    "error_type": "none"
                })]

            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to observe errors: {str(e)}")
            return [metrics.Observation(value=0, attributes={
                "method": "GET",
                "path": "/",
                "status_code": "200",
                "error_type": "none"
            })]

    def _observe_cart_items(self, options):
        """Real-time observer for cart items from database."""
        try:
            from app.core.database import SessionLocal
            from app.models.models import CartItem
            
            db = SessionLocal()
            try:
                # Get current cart totals for all users
                results = db.query(
                    CartItem.user_id,
                    func.coalesce(func.sum(CartItem.quantity), 0).label('total')
                ).group_by(CartItem.user_id).all()

                # Return measurements for each user
                return [
                    metrics.Observation(value=int(total), attributes={"user_id": str(user_id)})
                    for user_id, total in results
                ] or [metrics.Observation(value=0, attributes={"user_id": "0"})]

            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to observe cart items: {str(e)}")
            return [metrics.Observation(value=0, attributes={"user_id": "0"})]

    def track_request(self, method: str, path: str, status_code: int, duration_seconds: float):
        """Track request metrics.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            status_code: HTTP status code
            duration_seconds: Request duration in seconds
        """
        # Track request latency
        attributes = {
            "method": method,
            "path": path,
            "status_code": str(status_code)
        }
        self.request_latency.record(duration_seconds, attributes)
        
        # Store errors in database for real-time tracking
        if status_code >= 400:
            try:
                from app.core.database import SessionLocal
                
                error_type = "client" if status_code < 500 else "server"
                db = SessionLocal()
                try:
                    error_metric = self.ErrorMetric(
                        method=method,
                        path=path,
                        status_code=status_code,
                        error_type=error_type
                    )
                    db.add(error_metric)
                    db.commit()
                    logger.info(f"Stored error metric: method={method}, path={path}, status={status_code}, type={error_type}")
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"Failed to store error metric: {str(e)}")


class TelemetryMiddleware(BaseHTTPMiddleware):
    """Middleware for request telemetry."""
    
    async def dispatch(self, request: Request, call_next):
        if not settings.OTEL_ENABLED:
            return await call_next(request)
            
        start_time = time()
        response = await call_next(request)
        duration = time() - start_time
        
        if telemetry := get_telemetry():
            telemetry.track_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_seconds=duration
            )
            
        return response


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
        
        # Setup metrics with faster refresh
        resource = Resource.create({
            "service.name": settings.OTEL_SERVICE_NAME,
            "service.version": settings.APP_VERSION
        })

        reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(
                endpoint=settings.get_formatted_endpoint(),
                insecure=True if "localhost" in settings.OTEL_EXPORTER_OTLP_ENDPOINT else False,
                headers=settings.otel_headers_dict,
                timeout=5  # 5 second timeout
            ),
            export_interval_millis=1000  # 1 second refresh
        )

        provider = MeterProvider(
            metric_readers=[reader],
            resource=resource
        )
        
        metrics.set_meter_provider(provider)
        _telemetry = Telemetry(metrics.get_meter("xcart"))
        
        # Add telemetry middleware
        if app:
            app.add_middleware(TelemetryMiddleware)
            
        logger.info("OpenTelemetry initialized with real-time metrics")
            
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}")


# Global telemetry instance
_telemetry = None

def get_telemetry():
    """Get the global telemetry instance."""
    return _telemetry 