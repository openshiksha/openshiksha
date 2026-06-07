# Legacy Parity + Mobile Shell Closeout

## Summary

- Added self-service password change to Profile via `POST /api/v1/users/me/password/`.
- Added teacher question image upload via `POST /api/v1/questions/upload-image/`; URL paste remains available.
- Hardened mobile shell spacing and bottom-tab touch targets.
- Fixed a student assignment card shrink issue that caused horizontal overflow on phone-width dashboards.
- Updated initiative docs: legacy parity has no remaining user-facing TODOs, V2/mobile shell is closed for current scope, and IW-9/IW-10/IW-11 are deferred pending Widget Studio product validation.

## Verification

- `docker compose exec -T backend pytest --no-cov openshiksha/apps/api/tests/test_core_api.py::TestUserMeEndpoint openshiksha/apps/api/tests/test_core_api.py::TestQuestionSubpartImageUrl openshiksha/tests/test_admin_emails_env.py openshiksha/apps/core/tests/test_due_date_reminders.py`
- `npm test -- --run src/features/layout/BottomNav.test.tsx src/features/widgets/WidgetDevPage.test.tsx`
- `npm run type-check`
- Browser smoke at 390px wide using `student_demo` and `teacher_demo`: dashboard,
  profile, and question creator had no horizontal overflow; bottom tabs fit;
  profile password card and question image upload controls were visible.

## Product Notes

Developer-authored widgets remain the recommended path for new bespoke widget
kinds. They can be scaffolded with `npm run widget:new`, previewed in
`/widgets/dev`, and attached from the question creator once registered.

Widget Studio is not deleted; it is deliberately deferred. The next widget work
should start from product discovery around teacher-authored interactivity rather
than building IW-9/IW-10/IW-11 by inertia.
