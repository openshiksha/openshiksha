# Transactional emails

OpenShiksha sends a handful of transactional emails. Each one goes out as
**multipart/alternative**: a branded **HTML** body plus a **plain-text** fallback.
The HTML is rendered by a small, dependency-free layout module — no Django
templates, no MJML — mirroring the same string-catalog approach the rest of the
app uses for i18n.

## The emails

| Flow | Trigger | Recipient | Helper |
| --- | --- | --- | --- |
| Practice assignment | A remedial set is auto-created for a student | Student | `core.emails.notify_remedial_assigned` |
| Due-date reminder | Scheduled reminder before an assignment is due | Student | `core.emails.notify_due_date_reminder` |
| Graded | A submission finishes grading | Student | `core.emails.notify_grading_complete` |
| Weekly parent summary | Monday parent-digest batch | Parent | `ai.emails.notify_parent_weekly_summary` |
| New enquiry | Someone submits the public enquiry form | Site admins | `concierge.emails.notify_enquiry_received` |

All helpers are **fail-soft**: an SMTP error is logged, never raised, so email
problems can't break grading, the reminder batch, or the enquiry endpoint.

## Architecture

```
apps/core/email_layout.py     ← shared branded shell + components (the design system)
apps/core/emails.py           ← student emails  (+ en/hi content catalogs)
apps/ai/emails.py             ← parent weekly summary
apps/concierge/emails.py      ← admin enquiry notification
```

[`email_layout.py`](../backend/openshiksha/apps/core/email_layout.py) owns the
brand: tokens lifted from `frontend_modern/tailwind.config.js` (anchor orange
`#FF6F00`, warm "ink" neutrals, the graduation-cap keyhole logo) and a set of
reusable, email-client-safe components:

- `render_branded_email(...)` — the shell: accent bar, logo + wordmark header,
  emoji hero badge, serif heading, body, optional CTA button, footer.
- `button()`, `icon_badge()`, `score_ring()`, `info_panel()`, `paragraph()`.

Everything is **table-based and inline-styled** (the only `<style>` block holds a
couple of `@media` rules and resets) so it survives Gmail, Outlook and Apple
Mail. Colours, fonts and spacing are constants at the top of the module.

### Why HTML rides alongside plain text

The helpers still call Django's `send_mail(...)` / `mail_admins(...)` and pass the
pretty HTML as `html_message=`. The plain-text `message=` is unchanged. This:

- keeps a real text fallback (accessibility + deliverability), and
- means the rendered HTML is purely additive — **the existing email tests, which
  assert on the plain-text body, all still pass without modification**.

## Localization (LA-7)

Student and parent emails render in the recipient's `User.preferred_language`
(`en` / `hi`, default `en`). Each module keeps a tiny `dict` catalog
(`_STRINGS` for plain text, `_HTML` for the HTML chrome) and falls back to
English for any missing key — an untranslated email beats a broken one. The
concierge email is admin-facing and English-only.

## Settings

| Setting | Default | Purpose |
| --- | --- | --- |
| `EMAIL_BACKEND` | `console` (dev) | `…smtp.EmailBackend` to actually send |
| `EMAIL_HOST` / `EMAIL_PORT` / `EMAIL_USE_TLS` | `localhost` / `25` / `False` | SMTP transport |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | — | SMTP credentials |
| `DEFAULT_FROM_EMAIL` | `noreply@…` | From address |
| `EMAIL_LOGO_URL` | `https://openshiksha.org/brand/logo-orange.png` | Absolute logo URL (mail clients can't load app-relative paths) |
| `EMAIL_APP_URL` | `https://openshiksha.org` | Base URL for CTA buttons |

All are read from the environment in `settings/base.py`. `development.py` keeps
the **console** backend by default (nothing is sent — emails print to the
backend log), and only switches to real delivery when `EMAIL_BACKEND` is set in
the environment.

> **Logo / links are absolute.** For a local demo behind the cloudflared tunnel,
> point `EMAIL_LOGO_URL` / `EMAIL_APP_URL` at the tunnel URL; in production set
> them to the real domain.

## Adding a new branded email

1. Write the plain-text strings (and `en`/`hi` if user-facing) in the relevant
   `emails.py` catalog.
2. Build the HTML body with `layout.paragraph(...)` and any panels/badges.
3. Call `layout.render_branded_email(...)` and pass the result as
   `html_message=` to `send_mail(...)`.
4. Keep the helper fail-soft (`try/except`, log on failure).

## Previewing locally

With the dev stack running, render a helper's HTML to a file and open it in a
browser (or rely on the console backend, which prints the full message):

```python
# manage.py shell
import openshiksha.apps.core.emails as ce
from types import SimpleNamespace
captured = {}
ce.send_mail = lambda *a, **k: captured.update(html=k.get("html_message", ""))
ce.notify_grading_complete(
    SimpleNamespace(email="x@x.com", first_name="Asha", username="asha", preferred_language="en"),
    "Chapter 5 — Fractions", 85,
)
open("/app/preview.html", "w", encoding="utf-8").write(captured["html"])
```

## Tests

- `apps/core/tests/test_email_notifications.py` — student emails + localization.
- `apps/ai/tests/test_parent_intelligence.py` — parent weekly summary.
- `apps/concierge/tests/test_enquiry.py` — enquiry notification.

They run against the in-memory backend (`mail.outbox`) and assert on subjects,
recipients and the plain-text body.
