import os
from functools import wraps
from typing import Any, Callable

# OpenTelemetry imports
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

    HAS_OTEL = True
except ImportError:
    HAS_OTEL = False

# Prometheus imports
try:
    from prometheus_client import Counter, Gauge, Histogram

    HAS_PROM = True
except ImportError:
    HAS_PROM = False

# ==========================================
# 1. Prometheus Metrics Configuration
# ==========================================
if HAS_PROM:
    # Gauges
    QUEUE_DEPTH = Gauge(
        "codeorbit_queue_depth",
        "Current number of pending or queued tasks in SQLite/PostgreSQL queue",
    )
    WORKER_HEALTH = Gauge(
        "codeorbit_worker_health",
        "Status of workers in the pool (1 = healthy/active, 0 = inactive/dead)",
        ["worker_id", "hostname"],
    )
    CACHE_HIT_RATIO = Gauge(
        "codeorbit_cache_hit_ratio",
        "Cache hit ratio for prompt and tool caches",
        ["cache_type"],
    )

    # Counters
    TOKEN_USAGE = Counter(
        "codeorbit_token_usage_total",
        "Total LLM tokens consumed",
        ["model_name", "token_type"],  # token_type: prompt or completion
    )
    ERROR_RATES = Counter(
        "codeorbit_errors_total",
        "Total number of failures encountered",
        ["error_type", "source"],  # source: api, worker, scheduler
    )
    LLM_COSTS = Counter(
        "codeorbit_llm_costs_usd_total",
        "Total estimated cost in USD for LLM usage",
        ["model_name", "agent_name"],
    )

    # Histograms
    TASK_DURATION = Histogram(
        "codeorbit_task_duration_seconds",
        "Time taken to execute an entire workflow task",
        buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0),
    )
    MODEL_LATENCY = Histogram(
        "codeorbit_model_latency_seconds",
        "LLM API provider call roundtrip latency in seconds",
        ["model_name"],
        buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0),
    )
    API_RESPONSE_TIMES = Histogram(
        "codeorbit_api_response_time_seconds",
        "API gateway HTTP response latency",
        ["method", "path"],
        buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
    )
else:
    # Placeholders to prevent attribute errors if libraries are missing
    class MockMetric:
        def labels(self, *args, **kwargs):
            return self

        def inc(self, *args, **kwargs):
            pass

        def set(self, *args, **kwargs):
            pass

        def observe(self, *args, **kwargs):
            pass

        def time(self):
            return self

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    QUEUE_DEPTH = WORKER_HEALTH = CACHE_HIT_RATIO = MockMetric()
    TOKEN_USAGE = ERROR_RATES = LLM_COSTS = MockMetric()
    TASK_DURATION = MODEL_LATENCY = API_RESPONSE_TIMES = MockMetric()

# ==========================================
# 2. OpenTelemetry Tracing Setup
# ==========================================
tracer = None


def init_telemetry(service_name: str = "codeorbit-service") -> None:
    """
    Initialize OpenTelemetry trace configuration pointing to OTLP collector.
    Fails gracefully if libraries are missing or backend is offline.
    """
    global tracer
    if not HAS_OTEL:
        print("[WARNING] OpenTelemetry libraries not installed. Tracing is disabled.")
        return

    try:
        # Configure OTLP exporter to send to OTLP endpoint if explicitly set
        otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
        if not otlp_endpoint:
            # Set trace provider without OTLP span processors to disable background retry logs
            trace.set_tracer_provider(TracerProvider())
            tracer = trace.get_tracer("codeorbit")
            return

        # Set tracer provider
        resource = Resource.create(attributes={"service.name": service_name})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)

        # Register batch processor
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

        tracer = trace.get_tracer("codeorbit")
        print(
            f"[INFO] OpenTelemetry Tracing initialized for '{service_name}' -> {otlp_endpoint}"
        )
    except Exception as e:
        print(
            f"[WARNING] Failed to initialize OpenTelemetry Tracing: {e}. Falling back to default disabled state."
        )


# Fallback Tracer if OTel is disabled
class DummyTracer:
    class DummySpan:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def set_attribute(self, name, value):
            pass

        def record_exception(self, exception):
            pass

        def set_status(self, status):
            pass

    def start_as_current_span(self, name, *args, **kwargs):
        return self.DummySpan()


if not tracer:
    if HAS_OTEL:
        tracer = trace.get_tracer("codeorbit")
    else:
        tracer = DummyTracer()


# ==========================================
# 3. Span Tracing Decorator
# ==========================================
def trace_span(name: str):
    """
    Decorator to wrap a function run in an OpenTelemetry active span.
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if tracer:
                with tracer.start_as_current_span(name) as span:
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("module.name", func.__module__)
                    try:
                        result = func(*args, **kwargs)
                        return result
                    except Exception as e:
                        span.record_exception(e)
                        span.set_status(
                            trace.status.Status(trace.status.StatusCode.ERROR, str(e))
                        )
                        raise
            else:
                return func(*args, **kwargs)

        return wrapper

    return decorator
