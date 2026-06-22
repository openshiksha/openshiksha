"""Rate limiting for the OpenShiksha API.

DRF throttles are cache-backed (Redis in prod — see ``CACHES``), so counters are
shared across processes and survive restarts.

Two layers, configured in ``REST_FRAMEWORK`` (settings):

1. **Platform baseline** — ``AnonRateThrottle`` + ``UserRateThrottle`` apply to
   every API view (the ``anon`` / ``user`` scopes).
2. **Sensitive endpoints** — :class:`PathScopedThrottle` adds a *tighter* limit to
   login (brute-force defence) and the AI endpoints (they trigger paid LLM calls),
   keyed by path so we don't have to annotate the ~23 AI viewsets individually.

Both layers stack: an AI request is bounded by *both* the ``user`` rate and the
``ai`` rate (the lower one bites first).
"""

from __future__ import annotations

from rest_framework.throttling import ScopedRateThrottle, SimpleRateThrottle

# (path prefix, throttle scope). First match wins. Prefixes are the full request
# path under the API mount (`/api/v1/...`).
_PATH_SCOPES: tuple[tuple[str, str], ...] = (
    ("/api/v1/auth/login", "login"),
    ("/api/v1/auth/register", "login"),  # registration is the same abuse surface
    ("/api/v1/ai/", "ai"),
)


class PathScopedThrottle(ScopedRateThrottle):
    """Applies a per-path scope (``login`` / ``ai``) instead of a per-view one.

    Unlike the stock ``ScopedRateThrottle`` (which reads ``view.throttle_scope``),
    this derives the scope from the request path, so it can be dropped into the
    global ``DEFAULT_THROTTLE_CLASSES`` and cover whole endpoint groups without
    touching individual views. Returns ``True`` (not throttled by this class) for
    any path that isn't sensitive.
    """

    def allow_request(self, request, view):
        self.scope = next((scope for prefix, scope in _PATH_SCOPES if request.path.startswith(prefix)), None)
        if not self.scope:
            return True
        self.rate = self.get_rate()
        self.num_requests, self.duration = self.parse_rate(self.rate)
        # Skip ScopedRateThrottle.allow_request (it re-reads the view attr); run the
        # plain SimpleRateThrottle check with the scope/rate we just set.
        return SimpleRateThrottle.allow_request(self, request, view)

    def get_cache_key(self, request, view):
        # Key AI limits per user (so one heavy user can't starve others sharing an
        # IP); key anonymous limits (login/register) per client IP.
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
