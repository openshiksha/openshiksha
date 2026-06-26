"""
Request-scoped middleware (OBS-4).

``RequestIDMiddleware`` stamps every request with a correlation id (from an
incoming ``X-Request-ID`` header, or a fresh uuid4) that is threaded through the
logs (via the ContextVar in ``request_context``) and echoed back on the response.
When Sentry is active it also tags the current scope so an error and its log lines
share the same id.
"""

import uuid

from openshiksha.apps.core.request_context import reset_request_id, set_request_id

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        incoming = request.headers.get(REQUEST_ID_HEADER)
        request_id = incoming or uuid.uuid4().hex
        request.request_id = request_id
        token = set_request_id(request_id)
        self._tag_sentry(request_id)
        try:
            response = self.get_response(request)
        finally:
            # Always restore the previous context value, even on exceptions, so
            # the id never leaks into the next request on a reused worker.
            reset_request_id(token)
        response[REQUEST_ID_HEADER] = request_id
        return response

    @staticmethod
    def _tag_sentry(request_id: str) -> None:
        """Tag the Sentry scope with the request id — a no-op when Sentry is off.

        Soft-depends on OBS-3: guarded so it does nothing when sentry-sdk is not
        installed or no DSN was configured.
        """
        try:
            import sentry_sdk

            client = sentry_sdk.get_client()
            if client is not None and client.is_active():
                sentry_sdk.set_tag("request_id", request_id)
        except Exception:  # pragma: no cover - defensive; never break a request
            pass
