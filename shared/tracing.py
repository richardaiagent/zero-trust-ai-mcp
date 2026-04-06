# shared/tracing.py
# 역할: OpenTelemetry 분산 추적 설정
# 관련 챕터: Chapter 13

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor


def setup_tracing(service_name: str, otlp_endpoint: str = "http://jaeger:4317"):
    """OpenTelemetry + Jaeger 설정. 각 서비스 startup 시 호출."""
    provider = TracerProvider()
    exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    # FastAPI, httpx 자동 계측
    FastAPIInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()

    return trace.get_tracer(service_name)
