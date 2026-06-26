"""
Logging helpers (OBS-4): a request-id filter + an opt-in JSON formatter.

The filter injects the current correlation id onto every record so any formatter
can reference ``%(request_id)s``. The JSON formatter is selected only when
``LOG_FORMAT=json``; the default text formatters are left untouched.
"""

import json
import logging

from openshiksha.apps.core.request_context import get_request_id


class RequestIDFilter(logging.Filter):
    """Attach the current request's correlation id to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


class JSONFormatter(logging.Formatter):
    """Emit one JSON object per log line — friendly to log aggregators."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "time": self.formatTime(record),
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)
