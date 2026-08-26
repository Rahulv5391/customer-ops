import contextvars
import json
import logging
import time
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime

trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="-")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "trace_id": trace_id_var.get(),
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        extra_fields = getattr(record, "extra_fields", None)
        if extra_fields:
            payload.update(extra_fields)
        return json.dumps(payload)


def configure_logging(level: int = logging.INFO) -> None:
    logger = logging.getLogger("customerops")
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"customerops.{name}")


@contextmanager
def new_trace(existing_trace_id: str | None = None):
    token = trace_id_var.set(existing_trace_id or str(uuid.uuid4()))
    try:
        yield trace_id_var.get()
    finally:
        trace_id_var.reset(token)


@contextmanager
def timed(logger: logging.Logger, operation: str, **fields):
    start = time.perf_counter()
    try:
        yield
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        logger.warning(
            f"{operation} failed",
            extra={
                "extra_fields": {
                    **fields,
                    "elapsed_ms": elapsed_ms,
                    "status": "error",
                    "error_type": type(exc).__name__,
                }
            },
        )
        raise
    else:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        logger.info(
            f"{operation} completed",
            extra={"extra_fields": {**fields, "elapsed_ms": elapsed_ms, "status": "ok"}},
        )
