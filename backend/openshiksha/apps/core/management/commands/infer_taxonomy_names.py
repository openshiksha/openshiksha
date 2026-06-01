"""
Rename `Imported Subject %` and `Imported Chapter %` placeholders to canonical
NCERT-style names by inferring from each chapter's concept tags + content.

Pipeline per placeholder Chapter:
  1. **Concept signal** — gather all `concept` tags attached to questions/subparts
     in the chapter, plus salient nouns extracted from `question_text` /
     `solution_text` (LaTeX + stopwords stripped). Build a keyword bag.
  2. **NCERT cross-reference** — score the keyword bag against each candidate
     chapter name in `ncert_toc.json` for the known (standard, subject); pick
     the highest-scoring candidate above a threshold.
  3. **Subject inference** — `Imported Subject N` is mapped from
     `ncert_toc.json["subjects"]` directly (Cabinet subject IDs 1-5 are stable
     across the corpus).

Idempotent: skips any Chapter/Subject whose name no longer matches the
placeholder regex (never clobbers human edits). Writes an audit log JSON to
`apps/core/data/inferred_taxonomy_<date>.json`.

Run:
    python manage.py infer_taxonomy_names --dry-run    # print rename map
    python manage.py infer_taxonomy_names --apply      # write changes
"""

from __future__ import annotations

import datetime as _dt
import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterable

from django.core.management.base import BaseCommand
from django.db import transaction

from openshiksha.apps.core.models import Chapter, Subject

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_TOC_PATH = _DATA_DIR / "ncert_toc.json"

_CHAPTER_PLACEHOLDER = re.compile(r"^Imported Chapter\b", re.IGNORECASE)
_SUBJECT_PLACEHOLDER = re.compile(r"^Imported Subject\b", re.IGNORECASE)

# Tokens we never want in the keyword bag.
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "he",
    "her",
    "his",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "so",
    "that",
    "the",
    "their",
    "then",
    "there",
    "these",
    "they",
    "this",
    "to",
    "was",
    "were",
    "what",
    "when",
    "which",
    "who",
    "will",
    "with",
    "you",
    "your",
    "we",
    "our",
    "us",
    "but",
    "not",
    "no",
    "do",
    "does",
    "did",
    "find",
    "given",
    "show",
    "let",
    "let's",
    "use",
    "using",
    "value",
    "values",
    "answer",
    "question",
    "following",
    "above",
    "below",
    "between",
    "also",
    "any",
    "all",
    "each",
    "such",
    "than",
    "while",
    "after",
    "before",
    "where",
    "how",
    "why",
    "can",
    "could",
    "would",
    "should",
    "may",
    "might",
    "must",
    "shall",
    "had",
    "been",
    "being",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "first",
    "second",
    "third",
}

# Strip LaTeX delimiters + commands + the import template placeholders.
_LATEX_RE = re.compile(
    r"\$+[^$]*\$+|\\\([^)]*\\\)|\\\[[\s\S]*?\\\]|\\[a-zA-Z]+\{[^}]*\}|\\[a-zA-Z]+|\{\{[^}]+\}\}|\{[^}]*\}|<[^>]+>"
)
_NON_WORD = re.compile(r"[^a-zA-Z\s-]")
_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z-]{2,}")


def _tokenize(text: str) -> list[str]:
    if not text:
        return []
    stripped = _LATEX_RE.sub(" ", text)
    stripped = _NON_WORD.sub(" ", stripped)
    return [w.lower() for w in _WORD_RE.findall(stripped) if w.lower() not in _STOPWORDS]


def _candidate_tokens(name: str) -> set[str]:
    """NCERT chapter name → token set for scoring (singular forms approximated)."""
    tokens = set(_tokenize(name))
    # Cheap singularisation: strip trailing 's'.
    tokens |= {t[:-1] for t in tokens if t.endswith("s") and len(t) > 4}
    return tokens


def _load_toc() -> dict:
    with _TOC_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def _chapter_keyword_bag(chapter: Chapter) -> Counter[str]:
    """Aggregate concept tags + question/solution token counts for one chapter."""
    bag: Counter[str] = Counter()
    questions = chapter.questions.prefetch_related("tags", "subparts__tags").all()
    for q in questions:
        for tag in q.tags.all():
            if tag.tag_type == "concept":
                bag.update(_tokenize(tag.name.replace("-", " ").replace("_", " ")))
        for sp in q.subparts.all():
            for tag in sp.tags.all():
                if tag.tag_type == "concept":
                    bag.update(_tokenize(tag.name.replace("-", " ").replace("_", " ")))
            bag.update(_tokenize(sp.question_text or ""))
            bag.update(_tokenize(sp.solution_text or ""))
    return bag


def _score_candidate(bag: Counter[str], candidate_tokens: Iterable[str]) -> int:
    candidate_tokens = list(candidate_tokens)
    if not candidate_tokens:
        return 0
    return sum(bag.get(t, 0) for t in candidate_tokens)


def _infer_chapter_name(
    chapter: Chapter,
    toc: dict,
    min_score: int = 2,
) -> tuple[str | None, dict]:
    """Return (best_name, debug) or (None, debug) if no confident match."""
    bag = _chapter_keyword_bag(chapter)
    standard_key = str(chapter.standard.number)
    subject_name = chapter.subject.name
    candidates = (toc.get("chapters", {}).get(standard_key, {}) or {}).get(subject_name, [])

    if not candidates:
        return None, {"reason": "no-toc-entry", "standard": standard_key, "subject": subject_name}

    scored = []
    for name in candidates:
        tokens = _candidate_tokens(name)
        score = _score_candidate(bag, tokens)
        if score > 0:
            scored.append((score, name, sorted(tokens)))
    scored.sort(reverse=True)

    if not scored or scored[0][0] < min_score:
        return None, {"reason": "low-score", "top": scored[:3], "bag_size": sum(bag.values())}

    # Tie at the top? Don't guess.
    if len(scored) > 1 and scored[0][0] == scored[1][0]:
        return None, {"reason": "tie", "top": scored[:3]}

    return scored[0][1], {"reason": "match", "score": scored[0][0], "top": scored[:3]}


class Command(BaseCommand):
    help = "Rename Imported Subject/Chapter placeholders to canonical NCERT names."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Print rename map; write nothing.")
        parser.add_argument("--apply", action="store_true", help="Write inferred names.")
        parser.add_argument("--min-score", type=int, default=2, help="Minimum keyword-overlap score to accept.")

    def handle(self, *args, **opts):
        if not opts["dry_run"] and not opts["apply"]:
            self.stdout.write(self.style.ERROR("Pass --dry-run or --apply."))
            return

        toc = _load_toc()
        audit = {
            "started_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "mode": "apply" if opts["apply"] else "dry-run",
            "subjects": [],
            "chapters": [],
        }

        # --- Subjects ---
        for subject in Subject.objects.filter(name__iregex=r"^Imported Subject"):
            if not _SUBJECT_PLACEHOLDER.match(subject.name):
                continue
            new_name = toc.get("subjects", {}).get(subject.name)
            entry = {"id": subject.id, "old": subject.name, "new": new_name, "applied": False}
            if new_name and not Subject.objects.filter(name=new_name).exclude(id=subject.id).exists():
                if opts["apply"]:
                    subject.name = new_name
                    subject.save(update_fields=["name"])
                    entry["applied"] = True
                self.stdout.write(f"SUBJECT: {entry['old']} → {new_name}")
            elif new_name:
                entry["skipped"] = "target-name-exists"
                self.stdout.write(self.style.WARNING(f"skip subject {subject.name}: '{new_name}' already exists"))
            audit["subjects"].append(entry)

        # --- Chapters ---
        chapters = Chapter.objects.filter(name__iregex=r"^Imported Chapter").select_related("subject", "standard")
        for chapter in chapters:
            if not _CHAPTER_PLACEHOLDER.match(chapter.name):
                continue
            inferred, debug = _infer_chapter_name(chapter, toc, min_score=opts["min_score"])
            entry = {
                "id": chapter.id,
                "old": chapter.name,
                "subject": chapter.subject.name,
                "standard": chapter.standard.number,
                "new": inferred,
                "debug": debug,
                "applied": False,
            }
            if inferred:
                # Don't collide with an existing chapter under the same subject/standard.
                collides = (
                    Chapter.objects.filter(subject=chapter.subject, standard=chapter.standard, name=inferred)
                    .exclude(id=chapter.id)
                    .exists()
                )
                if collides:
                    entry["skipped"] = "target-name-exists"
                    self.stdout.write(self.style.WARNING(f"skip {chapter.name}: '{inferred}' already exists"))
                else:
                    if opts["apply"]:
                        with transaction.atomic():
                            chapter.name = inferred
                            chapter.save(update_fields=["name"])
                        entry["applied"] = True
                    self.stdout.write(f"CHAPTER {chapter.id}: {entry['old']} → {inferred} (score={debug.get('score')})")
            else:
                self.stdout.write(self.style.NOTICE(f"unmatched: {chapter.name} ({debug.get('reason')})"))
            audit["chapters"].append(entry)

        audit_path = _DATA_DIR / f"inferred_taxonomy_{_dt.date.today().isoformat()}.json"
        try:
            audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"Audit log: {audit_path}"))
        except OSError as exc:
            self.stdout.write(self.style.WARNING(f"Could not write audit log: {exc}"))

        matched = sum(1 for c in audit["chapters"] if c.get("applied") or (c.get("new") and not c.get("skipped")))
        self.stdout.write(
            self.style.SUCCESS(
                f"Done — {matched}/{len(audit['chapters'])} chapters inferred, "
                f"{sum(1 for s in audit['subjects'] if s.get('applied'))} subjects applied."
            )
        )
