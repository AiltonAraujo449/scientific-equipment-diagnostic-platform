
import contextvars
import json
import logging
from datetime import datetime, timezone

from prometheus_client import Counter, Histogram, make_asgi_app


DIAGNOSTICS_TOTAL = Counter(
    "sedp_diagnostics_total",
    "Total number of diagnostics executed.",
    ["outcome", "severity"],
)

DIAGNOSTIC_DURATION = Histogram(
    "sedp_diagnostic_duration_seconds",
    "Diagnostic processing duration in seconds.",
)

EVENTS_INGESTED = Counter(
    "sedp_events_ingested_total",
    "Total number of equipment events ingested.",
)

REQUEST_DURATION = Histogram(
    "sedp_api_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "endpoint", "status"],
)

metrics_app = make_asgi_app()

request_id_var = contextvars.ContextVar(
    "request_id",
    default="-",
)


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(
                record.exc_info
            )

        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler.addFilter(ContextFilter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
