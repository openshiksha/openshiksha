# Content packs — contribute questions to OpenShiksha

A **content pack** is a single JSON file that adds questions (optionally with
interactive widgets) to OpenShiksha's shared question bank. Packs are **data,
never code**: every pack is schema-validated by CI on your pull request, and
nothing you submit reaches a student until a maintainer has previewed and
approved it in-app.

See [`example-fractions-pack.json`](example-fractions-pack.json) for a
complete, valid pack — one MCQ plus one numeric question with a sandboxed
`number-line` widget.

## How it works

1. **Author** a pack (see the format below) and add it to this directory as
   `contrib/packs/<your-pack-name>.json`.
2. **Open a pull request.** CI validates every `contrib/packs/*.json` against
   the canonical schema and prints precise, per-field errors on failure — your
   pack self-checks before anyone reviews it.
3. **After merge**, a maintainer stages the pack into the review queue
   (`manage.py import_content_pack`). It sits there as *pending* — the live
   bank is untouched.
4. **In-app approval.** The maintainer previews your actual rendered questions
   and widgets in the admin review queue and clicks Approve. Only then do the
   questions materialize into the shared bank — published **with the
   attribution from your pack's `provenance` block**.

## Pack format (v1.0)

The canonical schema lives at
[`backend/openshiksha/apps/core/data/content_pack.schema.json`](../../backend/openshiksha/apps/core/data/content_pack.schema.json).
The essentials:

```jsonc
{
  "pack_version": "1.0",             // required, exactly "1.0"
  "name": "My pack",                 // optional, shown in the review queue
  "provenance": {                    // required — your attribution
    "author": "Your Name",           // required
    "license": "CC-BY-4.0",          // required — a license you can grant
    "source": "https://…",           // optional citation / origin URL
    "contact": "you@example.org"     // optional
  },
  "questions": [                     // required, at least one
    {
      "standard": 5,                 // grade 1..12
      "subject": "Mathematics",      // human-readable; resolved at import
      "chapter": "Fractions",
      "question_type": "mcq",        // mcq | fill_blank | matching | multi_select | numeric | short_answer | compound
      "difficulty": 2,               // 1 (easiest) .. 5 (hardest)
      "subparts": [
        {
          "index": 0,
          "question_text": "…",      // plain text or LaTeX
          "options": [{ "key": "A", "text": "…" }],   // MCQ only; null otherwise
          "correct_answer": { "type": "mcq", "answer": "A" },
          "widget_kind": "number-line",               // optional interactive widget
          "widget_config": { "min": 0, "max": 1, "step": 0.5 }
        }
      ]
    }
  ]
}
```

Widget-bearing subparts are double-validated: the pack schema first, then the
widget's own per-kind schema
([`backend/openshiksha/apps/core/data/widget_schemas/`](../../backend/openshiksha/apps/core/data/widget_schemas/)).
Available kinds: `number-line`, `fraction-bar`, `function-plotter`,
`thermo-piston`, `step-solver`.

## Validate locally before you push

```bash
cd backend
python manage.py validate_content_pack ../contrib/packs/your-pack.json
```

This is exactly the check CI runs — read-only, no database needed.

## Ground rules

- **Data only.** Packs carry question data and widget *config*. Widget *code*
  (a new widget kind) goes through normal code review — see the widget SDK
  guide and the widget-proposal issue form.
- **License honestly.** The `license` you declare is what the content is
  published under, and `author` is the credit it ships with. Only contribute
  content you have the right to offer.
- **One pack per PR** keeps review simple. A changed pack file is a *new* pack
  to the pipeline (identity is a content hash), so edits after approval need a
  fresh review round.
