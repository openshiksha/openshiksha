"""
Unit test for the ADMINS env-var parser in settings/base.py.

The parser turns a comma-separated `OPENSHIKSHA_ADMIN_EMAILS` value into the
list-of-tuples Django expects. Without this wiring, `mail_admins()` (called
by concierge `notify_enquiry_received`) silently no-ops in production.
"""

from openshiksha.settings.base import _parse_admin_emails


def test_empty_returns_empty_list():
    assert _parse_admin_emails("") == []
    assert _parse_admin_emails("   ") == []


def test_plain_emails():
    assert _parse_admin_emails("a@x.com,b@y.com") == [
        ("", "a@x.com"),
        ("", "b@y.com"),
    ]


def test_named_emails():
    assert _parse_admin_emails("Ops Team <ops@x.com>,Founder <f@y.com>") == [
        ("Ops Team", "ops@x.com"),
        ("Founder", "f@y.com"),
    ]


def test_mixed_named_and_plain():
    assert _parse_admin_emails("Ops <ops@x.com>,plain@y.com") == [
        ("Ops", "ops@x.com"),
        ("", "plain@y.com"),
    ]


def test_extra_whitespace_tolerated():
    assert _parse_admin_emails("  ops@x.com  ,  Founder <f@y.com>  ") == [
        ("", "ops@x.com"),
        ("Founder", "f@y.com"),
    ]


def test_skips_blank_entries():
    # Trailing comma, double comma, both stripped.
    assert _parse_admin_emails("a@x.com,,b@y.com,") == [
        ("", "a@x.com"),
        ("", "b@y.com"),
    ]
