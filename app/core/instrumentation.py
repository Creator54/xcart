from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from fastapi import FastAPI
from .config import settings
from .logging import get_logger

logger = get_logger("instrumentation")


def instrument_app(app: FastAPI) -> None:
    """Setup OpenTelemetry instrumentation for FastAPI"""
    logger.info("Setting up OpenTelemetry instrumentation...")

    # Configure the tracer
    resource = Resource.create(settings.otel_resource_attributes)
    tracer = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer)

    # Configure the OTLP exporter
    endpoint = settings.get_formatted_endpoint()
    if "localhost" in endpoint:
        otlp_exporter = OTLPSpanExporter(
            endpoint=endpoint,
            timeout=settings.OTEL_METRIC_EXPORT_TIMEOUT,
            insecure=True
        )
    else:
        otlp_exporter = OTLPSpanExporter(
            endpoint=endpoint,
            headers=settings.otel_headers_dict,
            timeout=settings.OTEL_METRIC_EXPORT_TIMEOUT,
        )
    tracer.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer)
    logger.info("OpenTelemetry instrumentation complete")
