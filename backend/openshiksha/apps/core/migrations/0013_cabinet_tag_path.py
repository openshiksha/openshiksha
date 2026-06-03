"""Data migration: rewrite legacy `cabinet:<question_id>` tags to the
chapter-scoped path `cabinet:c<chapter_id>:q<question_id>` (M7-05).

The legacy importer named every cabinet tag `cabinet:<question_id>` using only
the raw question-file basename, which collided across chapters that happened
to share an ID (e.g. `1.json` lives in dozens of chapter folders). The result
was 33 distinct source questions collapsed into one row with one tag.

This migration rewrites each existing `cabinet:<N>` tag to
`cabinet:c<chapter_id>:q<N>` using the first attached question's chapter FK,
so the surviving row gets a unique, chapter-scoped tag. On re-import after
this migration, the formerly-colliding questions will get *new* tags (because
the importer now generates the chapter-scoped name), so the 33 originally-
dropped questions reappear as fresh rows.

Reversible: `reverse_code` rewrites the new form back to the legacy form,
which may re-introduce collisions if a previous run dropped them — that's
acceptable because reversing a destructive collision recovery is also
destructive. The migration logs a count of rewritten tags via stdout.
"""

import re

from django.db import migrations

_LEGACY_RE = re.compile(r"^cabinet:([^:]+)$")
_NEW_RE = re.compile(r"^cabinet:c\d+:q(.+)$")


def rewrite_to_chapter_scoped(apps, schema_editor):
    QuestionTag = apps.get_model("core", "QuestionTag")
    rewritten = 0
    skipped_orphan = 0
    skipped_collision = 0

    legacy = list(QuestionTag.objects.filter(name__startswith="cabinet:"))
    for tag in legacy:
        m = _LEGACY_RE.match(tag.name)
        if not m:
            # Already chapter-scoped or some other cabinet:* tag — skip.
            continue
        question_id = m.group(1)
        first_q = tag.questions.first()
        if first_q is None:
            skipped_orphan += 1
            continue
        new_name = f"cabinet:c{first_q.chapter_id}:q{question_id}"
        if QuestionTag.objects.filter(name=new_name).exists():
            skipped_collision += 1
            continue
        tag.name = new_name
        tag.save(update_fields=["name"])
        rewritten += 1

    print(
        f"  cabinet_tag_path: rewrote {rewritten}, skipped_orphan={skipped_orphan}, "
        f"skipped_collision={skipped_collision}"
    )


def revert_to_legacy(apps, schema_editor):
    QuestionTag = apps.get_model("core", "QuestionTag")
    reverted = 0
    for tag in QuestionTag.objects.filter(name__startswith="cabinet:c"):
        m = _NEW_RE.match(tag.name)
        if not m:
            continue
        legacy_name = f"cabinet:{m.group(1)}"
        if QuestionTag.objects.filter(name=legacy_name).exists():
            continue
        tag.name = legacy_name
        tag.save(update_fields=["name"])
        reverted += 1
    print(f"  cabinet_tag_path (reverse): reverted {reverted}")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0012_user_email_reminders_opt_out_assignmentreminder"),
    ]

    operations = [
        migrations.RunPython(rewrite_to_chapter_scoped, reverse_code=revert_to_legacy),
    ]
