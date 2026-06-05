# ADMINS env-var wiring (concierge enquiry email activation)

**Classification:** Fix.

## Summary
The legacy-feature-parity audit flagged this as a small follow-up:
`concierge.emails.notify_enquiry_received` calls `mail_admins(...)`, but
Django's `ADMINS` setting was never declared anywhere in `settings/`. Result:
every enquiry no-op'd the email and the team only saw it via the Django
admin at `/admin/concierge/enquirer/`.

This PR loads `ADMINS` from an `OPENSHIKSHA_ADMIN_EMAILS` env var and parses
both `email@example.com` and `Name <email@example.com>` formats. Enquiries
now actually email the team whenever the env var is set.

## Files changed
- `backend/openshiksha/settings/base.py` — adds a `_parse_admin_emails`
  helper + reads `OPENSHIKSHA_ADMIN_EMAILS`. `MANAGERS = ADMINS` so Django's
  generic error mailer also benefits.
- `backend/openshiksha/tests/__init__.py` — new package marker.
- `backend/openshiksha/tests/test_admin_emails_env.py` — 6 unit tests
  covering empty, plain, named, mixed, whitespace, blank-skip parsing.

## Verification
- New tests: 6/6 pass.
- Existing `test_enquiry_notifies_admins` (which sets `settings.ADMINS` and
  checks `mail.outbox`) still passes — confirms the round-trip works once
  `ADMINS` is populated.
- `python manage.py check` clean.

## Deployment
Set `OPENSHIKSHA_ADMIN_EMAILS` in the production env. Examples:

```bash
# Single recipient
export OPENSHIKSHA_ADMIN_EMAILS="founder@openshiksha.edu.in"

# Multiple, with optional display names
export OPENSHIKSHA_ADMIN_EMAILS="Ops Team <ops@openshiksha.edu.in>,founder@openshiksha.edu.in"
```

Until set, behaviour is unchanged — emails no-op silently and enquiries
remain visible in the Django admin.

## Next
Question Bank chapter-filter UI, then M6-03 visual-regression baseline
activation.
