"""
Tests for request-correlation id middleware + JSON log formatter (OBS-4).
"""

import json
import logging

import pytest

from django.test import Client
from django.urls import reverse

from openshiksha.apps.core.logging_utils import JSONFormatter, RequestIDFilter
from openshiksha.apps.core.middleware import REQUEST_ID_HEADER
from openshiksha.apps.core.request_context import get_request_id, reset_request_id, set_request_id


@pytest.fixture
def client():
    return Client()


class TestRequestIDMiddleware:
    def test_round_trips_supplied_id(self, client):
        resp = client.get(reverse("healthz"), headers={"x-request-id": "abc-123"})
        assert resp[REQUEST_ID_HEADER] == "abc-123"

    def test_generates_id_when_absent(self, client):
        resp = client.get(reverse("healthz"))
        rid = resp[REQUEST_ID_HEADER]
        assert rid and rid != "-"
        # uuid4().hex → 32 hex chars
        assert len(rid) == 32

    def test_response_always_carries_header(self, client):
        resp = client.get(reverse("healthz"))
        assert REQUEST_ID_HEADER in resp

    def test_context_resets_between_requests(self, client):
        # Outside any request the contextvar is the default sentinel.
        assert get_request_id() == "-"
        client.get(reverse("healthz"), headers={"x-request-id": "first"})
        assert get_request_id() == "-"


class TestRequestContext:
    def test_set_get_reset(self):
        assert get_request_id() == "-"
        token = set_request_id("xyz")
        try:
            assert get_request_id() == "xyz"
        finally:
            reset_request_id(token)
        assert get_request_id() == "-"


class TestLoggingHelpers:
    def test_filter_injects_request_id(self):
        record = logging.LogRecord("t", logging.INFO, __file__, 1, "msg", None, None)
        token = set_request_id("req-7")
        try:
            assert RequestIDFilter().filter(record) is True
            assert record.request_id == "req-7"
        finally:
            reset_request_id(token)

    def test_json_formatter_emits_parseable_json_with_request_id(self):
        record = logging.LogRecord("apps", logging.WARNING, __file__, 1, "boom %s", ("x",), None)
        RequestIDFilter().filter(record)  # populate request_id
        line = JSONFormatter().format(record)
        parsed = json.loads(line)
        assert parsed["level"] == "WARNING"
        assert parsed["logger"] == "apps"
        assert parsed["message"] == "boom x"
        assert "request_id" in parsed

    def test_json_formatter_defaults_request_id_dash(self):
        record = logging.LogRecord("apps", logging.INFO, __file__, 1, "hi", None, None)
        parsed = json.loads(JSONFormatter().format(record))
        assert parsed["request_id"] == "-"
