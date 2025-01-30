from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from fastapi import FastAPI

def instrument_app(app: FastAPI) -> None:
    """Setup OpenTelemetry instrumentation for FastAPI"""
    
    # Configure the tracer
    resource = Resource.create({"service.name": "xcart"})
    tracer = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer)
    
    # Configure the OTLP exporter
    otlp_exporter = OTLPSpanExporter()
    tracer.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app) 