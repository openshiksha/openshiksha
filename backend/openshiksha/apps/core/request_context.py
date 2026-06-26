"""
Per-request correlation id, stored in a ContextVar (OBS-4).

A ``ContextVar`` is the right primitive here: it is isolated per thread *and* per
asyncio task (the app runs under Daphne/ASGI), so the id set by
``RequestIDMiddleware`` is visible to every log record emitted while handling that
request, without leaking across concurrent requests.
"""

import contextvars

_request_id_var: "contextvars.ContextVar[str]" = contextvars.ContextVar("request_id", default="-")


def get_request_id() -> str:
    """Return the current request's correlation id, or ``"-"`` outside a request."""
    return _request_id_var.get()


def set_request_id(value: str):
    """Set the correlation id for the current context; returns a reset token."""
    return _request_id_var.set(value)


def reset_request_id(token) -> None:
    """Restore the previous correlation id (call in a ``finally``)."""
    _request_id_var.reset(token)
