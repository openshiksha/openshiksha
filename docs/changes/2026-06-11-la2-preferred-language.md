# LA-2 — durable `preferred_language` end-to-end

**Date:** 2026-06-11
**Classification:** New
**Initiative:** [Language Access — i18n en/हिंदी](../initiatives/2026-language-access.md) (LA-2)

## Summary

The language choice now travels with the user. `User.preferred_language`
(en/hi, default en) is exposed on `GET /users/me/` and writable via
`PATCH /users/me/profile/`; the ProfilePage gets a Language selector; the
navbar switcher PATCHes the profile when authenticated; and at login the
profile preference seeds the UI locale on devices with no explicit override.

## Legacy files referenced

None — legacy had no user language preference of any kind (English-only
platform). Follows the `email_reminders_opt_out` precedent end-to-end.

## What changed and why

**Backend**
- `User.preferred_language = CharField(max_length=8, choices=en/hi,
  default="en")` + migration `0027_user_preferred_language` (additive,
  non-breaking).
- Field added to `UserSerializer`, `UserProfileUpdateSerializer`, the profile
  view's `ALLOWED_FIELDS` whitelist, and the User admin fieldset.

**Frontend**
- `User.preferred_language?: 'en' | 'hi'` type; `authApi.updateProfile`
  accepts it.
- `I18nProvider` gains the other two layers of the precedence contract
  (device localStorage > profile > 'en'):
  - `profileLocale` prop — seeds the locale when no device override exists.
    Seeding does **not** write localStorage (it isn't a device choice).
  - `onLocaleChange` callback — fired only on explicit switches (never on
    seeding); `App.tsx` uses it to PATCH the profile when authenticated,
    skipping when the profile already matches.
- `ProfilePage`: Language / भाषा `Select` (V2 primitive); saving applies the
  language to the live UI immediately via `setLocale`.

## Tests

- Backend (`test_profile_api.py` +4): default en on `/users/me/`, PATCH
  accepts en and hi, rejects `fr` with 400. Full suite green; missing-migration
  check (`makemigrations --check`) clean.
- Frontend: new `ProfilePage.test.tsx` (selector seeded from profile, payload
  includes `preferred_language`, saved language applied + persisted);
  `i18n.test.tsx` +3 (profile seeding without localStorage write, device
  override wins, `onLocaleChange` fires on switch but not on seed).
  Full suite 54 files / 342 tests green; lint/tsc/build/budget green
  (entry 96.97 kB).

## Migration notes

`0027_user_preferred_language` — additive column with default; safe to apply
live.

## Next steps

LA-3 (student chrome in Hindi), LA-4 (AI content language), LA-7 will reuse
`preferred_language` for localized emails.
