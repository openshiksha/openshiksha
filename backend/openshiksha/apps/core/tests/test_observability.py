"""
Tests for env-gated Sentry wiring + the secret scrubber (OBS-3).

No real network calls are made — `sentry_sdk.init` is monkeypatched.
"""

from openshiksha.apps.core import observability


class TestInitSentry:
    def test_noop_without_dsn(self, monkeypatch):
        monkeypatch.delenv("SENTRY_DSN", raising=False)
        assert observability.init_sentry() is False

    def test_inits_when_dsn_set(self, monkeypatch):
        monkeypatch.setenv("SENTRY_DSN", "https://example@o0.ingest.sentry.io/0")
        captured = {}

        def fake_init(**kwargs):
            captured.update(kwargs)

        import sentry_sdk

        monkeypatch.setattr(sentry_sdk, "init", fake_init)
        assert observability.init_sentry() is True
        # Gated config the prod posture depends on.
        assert captured["send_default_pii"] is False
        assert captured["before_send"] is observability._scrub
        assert len(captured["integrations"]) == 3


class TestScrub:
    def test_strips_authorization_header(self):
        event = {"request": {"headers": {"Authorization": "Bearer secrettoken", "Accept": "application/json"}}}
        scrubbed = observability._scrub(event, None)
        assert scrubbed["request"]["headers"]["Authorization"] == "[Filtered]"
        # Non-sensitive headers are preserved.
        assert scrubbed["request"]["headers"]["Accept"] == "application/json"

    def test_strips_cookies(self):
        event = {"request": {"cookies": "sessionid=abc"}}
        assert observability._scrub(event, None)["request"]["cookies"] == "[Filtered]"

    def test_strips_password_field_in_request_data(self):
        event = {"request": {"data": {"username": "alice", "password": "hunter2"}}}
        scrubbed = observability._scrub(event, None)
        assert scrubbed["request"]["data"]["password"] == "[Filtered]"
        assert scrubbed["request"]["data"]["username"] == "alice"

    def test_strips_nested_secret_in_extra(self):
        event = {"extra": {"config": {"api_key": "sk-123", "anthropic_token": "xyz", "safe": "ok"}}}
        scrubbed = observability._scrub(event, None)
        assert scrubbed["extra"]["config"]["api_key"] == "[Filtered]"
        assert scrubbed["extra"]["config"]["anthropic_token"] == "[Filtered]"
        assert scrubbed["extra"]["config"]["safe"] == "ok"

    def test_handles_event_without_request_or_extra(self):
        event = {"message": "boom"}
        assert observability._scrub(event, None) == {"message": "boom"}
