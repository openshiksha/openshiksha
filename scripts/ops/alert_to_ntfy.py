#!/usr/bin/env python3
"""Alertmanager → ntfy bridge (Production Observability Batch 4, ALT-2).

ntfy is not a native Alertmanager receiver: Alertmanager POSTs its own webhook
JSON schema, while ntfy wants a plain-text body plus ``Title``/``Tags``/
``Priority`` headers. This ~self-contained stdlib script is the standard glue —
it accepts an Alertmanager webhook POST on ``/alert`` and, for each alert in the
payload, POSTs a **single-line** message to ``ALERT_NTFY_URL``.

Deliberately dependency-light (``http.server`` + ``urllib.request`` only, **no new
pip dependency**) so it can run as a tiny sidecar / one-off Deployment next to
Alertmanager without dragging in a web framework. The Alertmanager config that
targets it lives at ``docs/ops/alertmanager/alertmanager.yml``.

Run::

    ALERT_NTFY_URL="https://ntfy.sh/<your-alerts-topic>" \\
        python3 scripts/ops/alert_to_ntfy.py            # listens on :9098

The payload→message mapping is factored into the pure ``format_alert`` /
``format_payload`` functions (no I/O), which is what makes this unit-testable —
see ``scripts/ops/tests/test_alert_to_ntfy.py``. The HTTP POST is the only seam.

Security: the ntfy URL is read from the environment and is **never** echoed to
logs (a leaked topic URL is a write capability to the channel).
"""

from __future__ import annotations

import json
import logging
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import request as urlrequest

logger = logging.getLogger("alert_to_ntfy")

# ntfy priority headers / tag emoji keyed by Alertmanager `severity` label. ntfy
# priorities: 5=max,4=high,3=default,2=low,1=min.
_SEVERITY_PRIORITY = {"critical": "high", "warning": "default", "info": "low"}
_SEVERITY_TAGS = {"critical": "rotating_light", "warning": "warning", "info": "information_source"}

# Listen address; in-cluster the Alertmanager webhook targets http://alert-to-ntfy:9098/alert.
LISTEN_HOST = os.getenv("ALERT_BRIDGE_HOST", "0.0.0.0")
LISTEN_PORT = int(os.getenv("ALERT_BRIDGE_PORT", "9098"))


def format_alert(alert: dict) -> tuple[str, str, dict[str, str]]:
    """Map a single Alertmanager alert dict to ``(title, body, headers)``.

    Pure (no I/O). ``headers`` carries the ntfy ``Title``/``Tags``/``Priority``.
    The body is forced to a **single line** (the project notification convention)
    by collapsing any embedded newlines.
    """
    labels = alert.get("labels") or {}
    annotations = alert.get("annotations") or {}

    status = (alert.get("status") or "firing").lower()
    severity = (labels.get("severity") or "info").lower()
    alertname = labels.get("alertname") or "UnknownAlert"

    resolved = status == "resolved"
    # Resolved notifications are always informational regardless of the original
    # severity — the bad thing stopped, so don't page for it.
    priority = "min" if resolved else _SEVERITY_PRIORITY.get(severity, "default")
    tag = "white_check_mark" if resolved else _SEVERITY_TAGS.get(severity, "bell")

    state = "RESOLVED" if resolved else "FIRING"
    title = f"[{state}] {alertname} ({severity})"

    summary = annotations.get("summary") or annotations.get("description") or alertname
    # Single line: collapse newlines + runs of whitespace so the push is one line.
    body = " ".join(str(summary).split())

    headers = {"Title": title, "Tags": tag, "Priority": priority}
    return title, body, headers


def format_payload(payload: dict) -> list[tuple[str, str, dict[str, str]]]:
    """Map a full Alertmanager webhook payload to a list of per-alert messages."""
    return [format_alert(a) for a in (payload.get("alerts") or [])]


def _sanitize_for_log(value: object) -> str:
    """Return a single-line, control-char-safe representation for logging."""
    text = str(value)
    text = text.replace("\r", " ").replace("\n", " ")
    return "".join(ch if ch.isprintable() else "?" for ch in text)


def _post_to_ntfy(ntfy_url: str, body: str, headers: dict[str, str]) -> None:
    """POST one formatted message to ntfy. Never logs the URL (write capability)."""
    req = urlrequest.Request(ntfy_url, data=body.encode("utf-8"), headers=headers, method="POST")
    with urlrequest.urlopen(req, timeout=10) as resp:  # noqa: S310 - operator-supplied env URL
        resp.read()


def _handle_payload(payload: dict, ntfy_url: str) -> int:
    """Format + push every alert in a payload. Returns the count pushed."""
    messages = format_payload(payload)
    for _title, body, headers in messages:
        try:
            _post_to_ntfy(ntfy_url, body, headers)
        except Exception:  # pragma: no cover - network failure path
            # Never include the URL in the log line.
            logger.warning(
                "alert_to_ntfy: failed to push alert %r",
                _sanitize_for_log(headers.get("Title", "")),
                exc_info=True,
            )
    return len(messages)


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802 - http.server API
        if self.path.rstrip("/") not in ("/alert", ""):
            self.send_error(404, "not found")
            return
        ntfy_url = os.getenv("ALERT_NTFY_URL")
        if not ntfy_url:
            self.send_error(500, "ALERT_NTFY_URL not configured")
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self.send_error(400, "invalid JSON")
            return
        count = _handle_payload(payload, ntfy_url)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(f"pushed {count} alert(s)\n".encode())

    def log_message(self, *args):  # silence default per-request stderr logging
        pass


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    if not os.getenv("ALERT_NTFY_URL"):
        logger.error("ALERT_NTFY_URL is not set; the bridge will reject requests with 500.")
    server = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), _Handler)
    logger.info("alert_to_ntfy listening on %s:%s", LISTEN_HOST, LISTEN_PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover
        server.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
