"""
OpenTelemetry tracing setup.
Exports traces to Jaeger via OTLP gRPC.
"""
from __future__ import annotations

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)

_tracer_provider: TracerProvider | None = None


def setup_tracing() -> None:
    """Initialize OpenTelemetry tracing with Jaeger OTLP export."""
    global _tracer_provider
    settings = get_settings()

    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        resource = Resource.create({
            "service.name": settings.otel_service_name,
            "service.version": "1.0.0",
            "deployment.environment": settings.app_env,
        })

        _tracer_provider = TracerProvider(resource=resource)

        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.otel_exporter_otlp_endpoint,
            insecure=True,
        )
        _tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        trace.set_tracer_provider(_tracer_provider)

        log.info(
            "tracing_initialized",
            endpoint=settings.otel_exporter_otlp_endpoint,
            service=settings.otel_service_name,
        )
    except Exception as e:
        log.warning("tracing_setup_failed", error=str(e), msg="Continuing without tracing")


def get_tracer(name: str) -> trace.Tracer:
    return trace.get_tracer(name)


def instrument_fastapi(app) -> None:
    """Attach FastAPI OTEL instrumentation."""
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)
        log.info("fastapi_instrumented")
    except Exception as e:
        log.warning("fastapi_instrumentation_failed", error=str(e))
