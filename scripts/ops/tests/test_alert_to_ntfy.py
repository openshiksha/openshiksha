"""Unit tests for the Alertmanager → ntfy bridge formatter (ALT-2).

The bridge's payload→(title, body, headers) mapping is a pure function, so these
tests need no network and no running server — they exercise ``format_alert`` /
``format_payload`` directly. The script lives outside the Django package
(``scripts/ops/``), so it is imported by path.

Run::

    python -m pytest scripts/ops/tests/test_alert_to_ntfy.py
"""

import importlib.util
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parent.parent / "alert_to_ntfy.py"
_spec = importlib.util.spec_from_file_location("alert_to_ntfy", _SCRIPT)
bridge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bridge)


def _alert(name, severity, status="firing", summary="Something happened", description=None):
    annotations = {"summary": summary}
    if description is not None:
        annotations["description"] = description
    return {
        "status": status,
        "labels": {"alertname": name, "severity": severity},
        "annotations": annotations,
    }


def test_critical_firing_maps_to_high_priority_rotating_light():
    title, body, headers = bridge.format_alert(
        _alert("OpenShikshaBackupStale", "critical", summary="Backup is stale (>36h)")
    )
    assert headers["Priority"] == "high"
    assert headers["Tags"] == "rotating_light"
    assert title == "[FIRING] OpenShikshaBackupStale (critical)"
    assert body == "Backup is stale (>36h)"
    assert headers["Title"] == title


def test_warning_firing_maps_to_default_priority_warning_tag():
    _title, _body, headers = bridge.format_alert(_alert("OpenShikshaGradeQueueBacklog", "warning"))
    assert headers["Priority"] == "default"
    assert headers["Tags"] == "warning"


def test_resolved_is_always_low_priority_with_check_mark():
    title, _body, headers = bridge.format_alert(
        _alert("OpenShikshaBackupStale", "critical", status="resolved")
    )
    # Resolution must NOT page even for a critical alert.
    assert headers["Priority"] == "min"
    assert headers["Tags"] == "white_check_mark"
    assert title.startswith("[RESOLVED]")


def test_body_is_collapsed_to_a_single_line():
    multiline = "Line one.\n  Line two.\n\nLine three."
    _title, body, _headers = bridge.format_alert(
        _alert("X", "warning", summary=multiline)
    )
    assert "\n" not in body
    assert body == "Line one. Line two. Line three."


def test_falls_back_to_description_then_alertname_for_body():
    # No summary -> description
    _t, body, _h = bridge.format_alert(
        {"status": "firing", "labels": {"alertname": "X", "severity": "warning"},
         "annotations": {"description": "from description"}}
    )
    assert body == "from description"
    # No annotations at all -> alertname
    _t2, body2, _h2 = bridge.format_alert(
        {"status": "firing", "labels": {"alertname": "OnlyName", "severity": "info"}}
    )
    assert body2 == "OnlyName"


def test_unknown_severity_defaults_safely():
    _t, _b, headers = bridge.format_alert(
        {"status": "firing", "labels": {"alertname": "X", "severity": "bogus"}, "annotations": {}}
    )
    assert headers["Priority"] == "default"
    assert headers["Tags"] == "bell"


def test_format_payload_handles_multiple_and_empty():
    payload = {
        "status": "firing",
        "alerts": [
            _alert("A", "critical"),
            _alert("B", "warning", status="resolved"),
        ],
    }
    msgs = bridge.format_payload(payload)
    assert len(msgs) == 2
    assert msgs[0][2]["Priority"] == "high"  # critical firing
    assert msgs[1][2]["Priority"] == "min"  # resolved
    assert bridge.format_payload({}) == []
    assert bridge.format_payload({"alerts": []}) == []
