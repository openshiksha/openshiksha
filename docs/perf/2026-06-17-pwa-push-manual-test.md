# Manual test — PWA Web Push due-date reminders

**Date:** 2026-06-17
**Covers:** MPN-1..5 (web push for due-date reminders)

Web push only works against a **production build / preview** — the dev server has
the service worker disabled (`devOptions.enabled: false`). Test in Chrome (or any
Chromium browser); on iOS, push requires an **installed** PWA on Safari 16.4+.

## One-time setup

1. Generate a VAPID keypair:
   ```bash
   cd backend && ./venv/Scripts/python.exe -m py_vapid --gen
   ```
   (or use any VAPID generator). Export the keys for the backend:
   ```bash
   export VAPID_PUBLIC_KEY=<base64url public key>
   export VAPID_PRIVATE_KEY=<PEM or base64url private key>
   export VAPID_ADMIN_EMAIL=admin@openshiksha.org
   ```
2. Build + serve the frontend so the SW is active:
   ```bash
   cd frontend_modern && npm run build && npm run preview
   ```
3. Run the backend (`runserver` / Docker) with the VAPID env vars set.

## Test steps

1. **Public key reachable** — `GET /api/v1/push/vapid-public-key/` returns a
   non-empty `publicKey`. (Empty ⇒ the frontend hides the push affordance, by
   design.)
2. **Subscribe** — log in as a student, accept the "Get reminders on your phone"
   prompt (MPN-4). Confirm a `PushSubscription` row appears in Django admin for
   that user.
   - Without MPN-4 merged, subscribe manually from DevTools console:
     `navigator.serviceWorker.ready.then(r => r.pushManager.subscribe({userVisibleOnly:true, applicationServerKey:<key>}))`
     then POST the result to `/api/v1/push/subscribe/`.
3. **Trigger a reminder** — create an assignment due within 24h for the student,
   then run the task:
   ```bash
   ./venv/Scripts/python.exe manage.py shell -c \
     "from openshiksha.apps.core.tasks import send_due_date_reminders; print(send_due_date_reminders())"
   ```
4. **Notification fires** — with the tab **closed/backgrounded**, the OS shows a
   notification: title "Assignment due soon", body naming the assignment + due
   date (localized to the student's `preferred_language`).
5. **Deep link on click** — tapping the notification focuses an open tab at, or
   opens, `/student/assignments/<id>`.
6. **Idempotency** — re-running the task does **not** fire a second notification
   (an `AssignmentReminder` row already exists).
7. **Stale prune** — unsubscribe in the browser, then trigger again; the backend
   gets a 410 and deletes the stale `PushSubscription` row (no error in the task).
8. **Opt-out** — set the student's reminders opt-out (ProfilePage toggle / admin);
   trigger again → neither email nor push is sent.

## Expected results checklist

- [ ] vapid-public-key returns a key
- [ ] subscribe creates a row; re-subscribe upserts (no duplicate)
- [ ] notification appears with the app closed, localized
- [ ] click deep-links to the assignment
- [ ] re-run does not duplicate
- [ ] unsubscribe → stale row pruned on next send
- [ ] opt-out suppresses both channels
