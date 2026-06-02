# M7-06 — Inline-image extraction in importer + renderer `<img>` allowlist

## Summary

Recovers inline images embedded in Cabinet HTML question/solution/hint bodies and
hardens the renderer so only http(s) image sources survive.

**Key data finding:** the entire Cabinet bank contains **zero** `<img src>` tags.
Cabinet's actual inline-image mechanism is the `#{filename}#` token, and it is
currently dropped — it leaks to the rendered output as the literal text
`#{8.gif}#`. The original plan's `<img src>` premise didn't match the data; this
PR ports the *real* format (the `#{}#` token) while still handling relative
`<img src>` defensively for any future content.

## Classification

**Improve** — restores inline-image fidelity (the legacy Cabinet microservice
resolved `#{}#` tokens; the modern importer had been silently dropping them) and
self-hosts the content with no microservice.

## Legacy files referenced

- `cabinet/cabinet_api.py` — `build_image()` / the original `#{}#` token
  resolution against the Cabinet filesystem.

## What changed

### Importer — `backend/openshiksha/apps/core/management/commands/import_cabinet_questions.py`
- `rewrite_inline_images(text, raw_dir, chapter_base)` — rewrites:
  - `#{name.ext}#` token → `<img src="<abs>" alt="name.ext">`
  - relative `<img src="x">` → absolute `<img src="<abs>">`
  - absolute http(s) `src` → untouched
  - unresolvable reference → left as-is (never invents a broken URL; the fidelity
    audit can flag the residual).
- `_resolve_inline_filename()` resolves a filename against the chapter raw dir
  (sibling first, then `img/` subdir), mirroring `_find_subpart_image`.
- Wired into `_import_container` over `question_text`/`solution_text`/`hint_text`;
  reused the new `chapter_base` to de-duplicate the sibling-image URL build.
- New `inline_images` stat in the report line.

### Renderer — `frontend_modern/src/shared/ui/renderRichContent.ts`
- Added a `afterSanitizeAttributes` DOMPurify hook (registered once) that drops
  any `<img src>` not matching `^https?://`. Blocks `data:` SVG XSS payloads and
  guarantees no relative leftover resolves wrongly. `img`/`src` were already in
  the allowlist.

## Materialising on existing data

The importer change only affects rows processed after it lands. The importer is
idempotent (re-runs update existing Questions via the `cabinet:c<chap>:q<id>`
tag), so the closing re-import step of the daily plan is what fixes live data.
No one-off data migration — re-import is the single source of truth.

## Tests

### Backend — `test_import_cabinet.py`
- `TestInlineImageRewrite` (6 pure tests): `#{}#` → img/ subdir, → sibling,
  unresolvable left untouched, relative `<img src>` rewritten, absolute untouched,
  empty text.
- `test_inline_image_token_rewritten_to_absolute_img` (DB): new fixture question
  1006 (`#{organ.png}#` + `img/organ.png`) imports with an absolute `<img>` tag
  and no leftover token.
- Updated `test_malformed_question_skipped` / `test_idempotent_reimport` for the
  5th valid fixture question.

### Frontend — `RichContent.test.tsx`
- https/http src kept; relative src dropped; `data:` SVG src dropped.

Full backend suite: **709 passed, 92.96%**. Frontend: type-check, lint, 21
RichContent tests, and build all green.

## Migration notes

None — no schema change.

## Next steps

- PR 3: M7-03a per-subpart `subpart_type` (backend).
- Closing re-import will materialise inline images on the live corpus.
