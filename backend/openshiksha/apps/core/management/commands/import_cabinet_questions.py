"""
Management command: import_cabinet_questions

Imports the legacy openshiksha-cabinet question bank into the modern Django DB.

Legacy questions lived in the Cabinet microservice — an external HTTP filesystem
that Django queried live at render/grade time. This command performs a one-time
migration of that content directly into the DB, removing the runtime dependency.

Cabinet on-disk layout (a local clone of openshiksha-cabinet):

    questions/containers/<board>/<school>/<standard>/<subject_id>/<chapter_id>/<question_id>.json
    questions/raw/<board>/<school>/<standard>/<subject_id>/<chapter_id>/<subpart_id>.json

A container lists its subpart IDs: ``{"subparts": [101, 102], "hint": null}``.
Each subpart JSON carries: ``type``, ``content.text``, ``options`` (correct/incorrect),
``answer``, ``variable_constraints``, ``solution.text``, ``hint.text``.

Conversions (legacy -> modern):
  - tokens:      ``_{a}_`` -> ``{{a}}``  and  ``_{{expr}}_`` -> ``{{expr}}``
  - power:       ``pow(a, b)`` -> ``(a)**(b)``  (modern safe_eval_expr has no pow())
  - constraints: ``{"range": {"include": [[1, 6]]}}`` -> ``{"min": 1, "max": 6, "integer": true}``
  - options:     ``{"correct": ..., "incorrect": [...]}`` -> ``[{"key": "A", "text": ...}, ...]``
  - cabinet type 1->mcq, 2->multi_select, 3->numeric, 4->fill_blank

Usage:
    python manage.py import_cabinet_questions --source /path/to/openshiksha-cabinet/questions
    python manage.py import_cabinet_questions --source <dir> --dry-run
    python manage.py import_cabinet_questions --source <dir> --mapping mapping.json --limit 10
"""

from __future__ import annotations

import ast
import json
import re
from collections import Counter
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from openshiksha.apps.api.croupier import _SAFE_CONSTS, _SAFE_FUNCS
from openshiksha.apps.core.models import (
    Chapter,
    Question,
    QuestionSubpart,
    QuestionTag,
    QuestionType,
    Standard,
    Subject,
)

# ─────────────────────────────────────────────────────────────
# Cabinet type -> modern QuestionType
# ─────────────────────────────────────────────────────────────

CABINET_TYPE_MAP = {
    1: QuestionType.MCQ,
    2: QuestionType.MULTI_SELECT,
    3: QuestionType.NUMERIC,
    4: QuestionType.FILL_BLANK,
}

_OPTION_KEYS = [chr(ord("A") + i) for i in range(26)]

DEFAULT_CONSTRAINT = {"min": 1, "max": 9, "integer": True}

# Bundled curated subject/chapter names — used as the default mapping so a plain
# import produces proper taxonomy (not "Imported Subject/Chapter N" placeholders).
_DEFAULT_TAXONOMY_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "cabinet_taxonomy.json"

# Image extensions Cabinet uses (PNG dominates; JPG/SVG occasionally).
_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".svg")

# Public raw URL for the cabinet repo; raw.githubusercontent.com serves directly.
_CABINET_RAW_BASE = "https://raw.githubusercontent.com/openshiksha/openshiksha-cabinet/HEAD/questions/raw"


# Cabinet's inline-image mechanisms inside HTML question/solution/hint bodies:
#   - `#{8.gif}#` token (the actual format used by authors), and
#   - a relative `<img src="x.png">` (defensive — none exist in the current bank
#     but the rewrite is correct if any are added later).
# Both resolve to an absolute raw.githubusercontent.com URL so the content is
# self-hosted with no Cabinet microservice. Absolute http(s) srcs are untouched.
_INLINE_IMG_TOKEN = re.compile(r"#\{([^{}#]+)\}#")
_REL_IMG_SRC = re.compile(r'(<img\b[^>]*?\bsrc=")(?!https?://)([^"]+)(")', re.IGNORECASE)


def _resolve_inline_filename(raw_dir, filename: str) -> "str | None":
    """Return the chapter-relative subpath for an inline image filename, or None.

    Mirrors ``_find_subpart_image``: checks a sibling of the JSON first, then the
    ``img/`` subdirectory (Cabinet's two storage conventions).
    """
    if (raw_dir / filename).is_file():
        return filename
    if (raw_dir / "img" / filename).is_file():
        return f"img/{filename}"
    return None


def rewrite_inline_images(text: str, raw_dir, chapter_base: str) -> str:
    """Rewrite Cabinet inline image references to absolute raw-GitHub ``<img>`` tags.

    - ``#{name.ext}#`` token  → ``<img src="<abs>" alt="name.ext">``
    - relative ``<img src="x">`` → absolute ``<img src="<abs>">``

    ``chapter_base`` is the raw URL prefix up to the chapter directory. A
    reference that can't be resolved on disk is left untouched (so the importer
    never invents a broken URL; the fidelity audit can flag the residual).
    """
    if not text:
        return text or ""

    def _token(m: "re.Match[str]") -> str:
        fn = m.group(1).strip()
        rel = _resolve_inline_filename(raw_dir, fn)
        if rel is None:
            return m.group(0)
        return f'<img src="{chapter_base}/{rel}" alt="{fn}">'

    def _relsrc(m: "re.Match[str]") -> str:
        fn = m.group(2).strip()
        rel = _resolve_inline_filename(raw_dir, fn)
        if rel is None:
            return m.group(0)
        return f"{m.group(1)}{chapter_base}/{rel}{m.group(3)}"

    text = _INLINE_IMG_TOKEN.sub(_token, text)
    text = _REL_IMG_SRC.sub(_relsrc, text)
    return text


# M7-11: an authored interactive widget is detected by an embedded <script> or
# an inline event handler (on*=). Static <svg> diagrams have neither and stay on
# the normal sanitised path.
_INTERACTIVE_RE = re.compile(r"<script\b|\bon[a-z]+\s*=", re.IGNORECASE)
_SCRIPT_BLOCK_RE = re.compile(r"<script\b[^>]*>.*?</script\s*>", re.IGNORECASE | re.DOTALL)
_EVENT_HANDLER_RE = re.compile(r"""\son[a-z]+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)""", re.IGNORECASE)


def is_interactive_html(text: str) -> bool:
    """True when ``text`` carries an authored interactive widget (script/handler)."""
    return bool(text) and bool(_INTERACTIVE_RE.search(text))


def strip_interactive(text: str) -> str:
    """Remove <script> blocks and inline event handlers — the safe fallback that
    goes into ``question_text``. (DOMPurify strips these again at render; storing
    a clean copy keeps the raw widget HTML out of the normal render path.)"""
    if not text:
        return text or ""
    text = _SCRIPT_BLOCK_RE.sub("", text)
    text = _EVENT_HANDLER_RE.sub("", text)
    return text


def resolve_inline_image_urls(text: str, raw_dir, chapter_base: str) -> str:
    """Replace ``#{name.ext}#`` tokens with the **bare** absolute raw-GitHub URL.

    Unlike ``rewrite_inline_images`` (which emits ``<img>`` tags for prose), this
    leaves the URL bare because in interactive widgets the token appears inside
    JS string literals / attribute values (e.g. ``attr('src','#{8.gif}#')``).
    Unresolvable tokens are left untouched.
    """
    if not text:
        return text or ""

    def _token(m: "re.Match[str]") -> str:
        fn = m.group(1).strip()
        rel = _resolve_inline_filename(raw_dir, fn)
        if rel is None:
            return m.group(0)
        return f"{chapter_base}/{rel}"

    return _INLINE_IMG_TOKEN.sub(_token, text)


def _find_subpart_image(raw_dir, sp_id) -> "tuple[str, str] | None":
    """
    Locate the image (if any) belonging to a cabinet subpart.

    Cabinet stores images two ways depending on the chapter:
      - sibling file:  ``raw/<...>/<chapter>/<sp_id>.png``
      - img/ subdir:   ``raw/<...>/<chapter>/img/<sp_id>.png``

    Returns ``(relative_subpath, ext)`` on success so the caller can build the
    raw.githubusercontent.com URL, or ``None`` if no image exists.
    """
    for ext in _IMAGE_EXTS:
        sibling = raw_dir / f"{sp_id}{ext}"
        if sibling.is_file():
            return (f"{sp_id}{ext}", ext.lstrip("."))
        nested = raw_dir / "img" / f"{sp_id}{ext}"
        if nested.is_file():
            return (f"img/{sp_id}{ext}", ext.lstrip("."))
    return None


# ─────────────────────────────────────────────────────────────
# Pure conversion helpers (unit-tested in test_import_cabinet.py)
# ─────────────────────────────────────────────────────────────

# _{{expr}}_  ->  {{expr}}   (expression token: capture the inner expression and re-wrap in {{...}})
_EXPR_TOKEN = re.compile(r"_\{\{([^{}]+)\}\}_")
# _{name}_  ->  {{name}}     (variable token: valid identifier only)
_VAR_TOKEN = re.compile(r"_\{([a-zA-Z_]\w*)\}_")
# pow(a, b) -> (a)**(b)      (innermost first; applied repeatedly for nesting)
_POW_CALL = re.compile(r"pow\(\s*([^(),]+?)\s*,\s*([^(),]+?)\s*\)")


def convert_tokens(text: str) -> str:
    """Rewrite legacy ``_{x}_`` / ``_{{expr}}_`` substitution tokens to ``{{...}}``.

    Modern croupier matches only the ``{{...}}`` form; the previous
    implementation emitted ``{...}`` (single braces) for expression tokens,
    so they leaked to the rendered output. Fixed 2026-05-30.
    """
    if not text:
        return text or ""
    text = _EXPR_TOKEN.sub(r"{{\1}}", text)
    text = _VAR_TOKEN.sub(r"{{\1}}", text)
    return text


def convert_pow(expr: str) -> str:
    """
    Rewrite Python-2 ``pow(base, exp)`` calls to ``(base)**(exp)``.

    Applied repeatedly so simple nestings collapse. Args containing nested
    parens/commas are left untouched (the regex only matches atomic args) so an
    ambiguous expression is preserved rather than corrupted.
    """
    if not expr:
        return expr or ""
    previous = None
    current = expr
    # Iterate until stable, capped to avoid pathological loops.
    for _ in range(10):
        if current == previous:
            break
        previous = current
        current = _POW_CALL.sub(r"(\1)**(\2)", current)
    return current


def convert_expression(text: str) -> str:
    """Token + power conversion for any field that may carry math expressions."""
    return convert_pow(convert_tokens(text))


def convert_constraints(raw: dict | None) -> dict:
    """
    Convert a single legacy variable constraint to ``{"min", "max", "integer"}``.

    Legacy unconstrained (``{}`` / ``None``) -> sensible default. Multi-range
    ``include`` lists collapse to the union (overall min / overall max).
    """
    if not raw:
        return dict(DEFAULT_CONSTRAINT)

    include = (raw.get("range") or {}).get("include")
    if not include:
        return dict(DEFAULT_CONSTRAINT)

    lows = [pair[0] for pair in include if isinstance(pair, (list, tuple)) and len(pair) == 2]
    highs = [pair[1] for pair in include if isinstance(pair, (list, tuple)) and len(pair) == 2]
    if not lows or not highs:
        return dict(DEFAULT_CONSTRAINT)

    lo, hi = min(lows), max(highs)
    integer = all(float(v).is_integer() for v in (lo, hi))
    return {"min": lo, "max": hi, "integer": integer}


def convert_all_constraints(raw: dict | None) -> dict | None:
    """Convert a whole ``{var: legacy_constraint}`` map. Tokens in names are stripped."""
    if not raw:
        return None
    out: dict = {}
    for name, spec in raw.items():
        clean = name.strip("_").strip("{}")
        out[clean] = convert_constraints(spec if isinstance(spec, dict) else None)
    return out or None


def _option_text(item) -> str:
    """A cabinet option is ``{"text": "..."}`` (or occasionally a bare string)."""
    if isinstance(item, dict):
        return convert_expression(str(item.get("text", "")))
    return convert_expression(str(item))


def convert_options(options: dict | None, cabinet_type: int) -> tuple[list[dict] | None, str | list[str]]:
    """
    Convert cabinet ``options`` (correct/incorrect) into modern keyed options.

    Returns ``(options_list, correct)`` where ``correct`` is a single key for
    MCQ or a list of keys for multi_select. Options are concatenated as
    [correct..., incorrect...] and keyed A, B, C, ...; the per-student Croupier
    shuffle randomizes display order at serve time, so storage order is moot.
    """
    if not options:
        return None, ""

    correct_raw = options.get("correct")
    incorrect_raw = options.get("incorrect") or []

    correct_items: list = []
    if cabinet_type == 2:  # multi_select: correct is a list
        correct_items = list(correct_raw or [])
    elif correct_raw is not None:  # mcq: correct is a single object
        correct_items = [correct_raw]

    ordered = correct_items + list(incorrect_raw)
    option_list = [{"key": _OPTION_KEYS[i], "text": _option_text(item)} for i, item in enumerate(ordered)]
    correct_keys = [_OPTION_KEYS[i] for i in range(len(correct_items))]

    if cabinet_type == 2:
        return option_list, correct_keys
    return option_list, (correct_keys[0] if correct_keys else "")


def convert_subpart(data: dict, index: int) -> dict:
    """
    Convert one cabinet subpart JSON into kwargs for a ``QuestionSubpart``.

    Raises ``ValueError`` for an unrecognized cabinet type so the caller can
    skip the question without aborting the whole import.
    """
    cabinet_type = data.get("type")
    if cabinet_type not in CABINET_TYPE_MAP:
        raise ValueError(f"unknown cabinet type {cabinet_type!r}")
    q_type = CABINET_TYPE_MAP[cabinet_type]

    raw_content = str((data.get("content") or {}).get("text", ""))
    # M7-11: an authored interactive widget (embedded <script>/event handlers) is
    # preserved verbatim for the sandboxed iframe renderer; question_text holds a
    # script-free fallback. Variable tokens are converted to {{var}} (the
    # serializer substitutes them per student); image #{...}# tokens stay raw here
    # and are resolved to bare URLs by the caller (which knows the chapter dir).
    interactive = is_interactive_html(raw_content)
    if interactive:
        interactive_html = convert_tokens(raw_content)
        question_text = convert_expression(strip_interactive(raw_content))
    else:
        interactive_html = ""
        question_text = convert_expression(raw_content)

    solution_text = convert_expression(str((data.get("solution") or {}).get("text", "")))
    hint_text = convert_expression(str((data.get("hint") or {}).get("text", "")))
    variable_constraints = convert_all_constraints(data.get("variable_constraints"))

    options: list[dict] | None = None
    if cabinet_type in (1, 2):
        options, correct = convert_options(data.get("options"), cabinet_type)
        correct_answer = {"type": q_type.value, "answer": correct}
    elif cabinet_type == 3:  # numeric: answer is {"value": "<expr>"}
        answer = data.get("answer") or {}
        value = answer.get("value") if isinstance(answer, dict) else answer
        correct_answer = {"type": q_type.value, "answer": convert_expression(str(value or ""))}
    else:  # fill_blank: answer is a plain string
        correct_answer = {"type": q_type.value, "answer": convert_expression(str(data.get("answer") or ""))}

    return {
        "index": index,
        "subpart_type": q_type.value,  # M7-03: per-subpart type, from the cabinet `type`.
        "question_text": question_text,
        "options": options,
        "correct_answer": correct_answer,
        "variable_constraints": variable_constraints,
        "solution_text": solution_text,
        "hint_text": hint_text,
        "is_interactive": interactive,
        "interactive_html": interactive_html,
        "_question_type": q_type,
    }


# ─────────────────────────────────────────────────────────────
# Shared stem extraction (M7-07)
# ─────────────────────────────────────────────────────────────


def _split_leading_paragraph(text: str) -> "tuple[str, str]":
    """Return (leading paragraph, remainder).

    A "paragraph" is either an HTML `<p>…</p>` block (Cabinet's most common
    shape) or everything before the first double newline. If neither is
    present, returns ("", text).
    """
    if not text:
        return "", ""
    stripped = text.lstrip()
    # HTML <p>...</p> at the start.
    if stripped.startswith("<p>"):
        end = stripped.find("</p>")
        if end != -1:
            head = stripped[: end + len("</p>")]
            tail = stripped[end + len("</p>") :].lstrip()
            return head, tail
    # Double newline split.
    parts = text.split("\n\n", 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].lstrip()
    return "", text


def _lift_shared_stem(converted_subparts: list[dict]) -> str:
    """If every subpart's `question_text` starts with the same paragraph, lift
    it out and strip it from each subpart. Mutates `converted_subparts` in
    place. Returns the lifted stem (or empty string when there's none)."""
    if len(converted_subparts) < 2:
        return ""
    heads_tails = [_split_leading_paragraph(sp.get("question_text", "")) for sp in converted_subparts]
    heads = [h for h, _ in heads_tails]
    if not heads[0] or any(h != heads[0] for h in heads):
        return ""
    # Require a stem of at least 20 chars to avoid lifting tiny labels.
    if len(heads[0].strip()) < 20:
        return ""
    for sp, (_h, tail) in zip(converted_subparts, heads_tails):
        sp["question_text"] = tail
    return heads[0]


# ─────────────────────────────────────────────────────────────
# Expression coverage scan (M7-08)
# ─────────────────────────────────────────────────────────────

# Same token pattern as the runtime substituter (croupier._TOKEN_RE) — kept
# here as a local copy so the scanner doesn't depend on a private name.
_TOKEN_RE = re.compile(r"\{\{([^{}]+)\}\}")


def _iter_expressions(subpart_fields: dict):
    """Yield every ``{{...}}`` inner expression from a converted subpart.

    Walks ``question_text``, ``solution_text``, ``hint_text``, each option's
    ``text``, and the ``correct_answer.answer`` string(s). Bare-identifier
    tokens are included — they're still names the scanner must classify.
    """
    for field in ("question_text", "solution_text", "hint_text"):
        for m in _TOKEN_RE.finditer(subpart_fields.get(field) or ""):
            yield m.group(1).strip()
    for opt in subpart_fields.get("options") or []:
        for m in _TOKEN_RE.finditer(opt.get("text") or ""):
            yield m.group(1).strip()
    correct = (subpart_fields.get("correct_answer") or {}).get("answer")
    if isinstance(correct, str):
        for m in _TOKEN_RE.finditer(correct):
            yield m.group(1).strip()
    elif isinstance(correct, list):
        # multi_select: each entry is a key string, but defensive in case
        # an expression token ever leaks in.
        for entry in correct:
            if isinstance(entry, str):
                for m in _TOKEN_RE.finditer(entry):
                    yield m.group(1).strip()


def _collect_unknown_names(expr: str, declared_vars: set[str]) -> list[str]:
    """Parse ``expr`` and return any ``ast.Name`` ids that are neither a
    declared variable, an allowlisted constant, nor an allowlisted function.

    A malformed expression yields an empty list — the caller already reports
    such tokens separately as un-substituted.
    """
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        return []
    unknown: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            name = node.id
            if name in declared_vars or name in _SAFE_CONSTS or name in _SAFE_FUNCS:
                continue
            # Dunder names are never safe — surface them loudly.
            unknown.append(name)
    return unknown


# ─────────────────────────────────────────────────────────────
# Command
# ─────────────────────────────────────────────────────────────


class Command(BaseCommand):
    help = "Import legacy openshiksha-cabinet questions into the modern DB."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            required=True,
            help="Path to the cabinet 'questions' directory (a local clone of openshiksha-cabinet).",
        )
        parser.add_argument(
            "--mapping",
            default=None,
            help="Optional JSON file mapping legacy IDs to names: "
            '{"subjects": {"12": "Mathematics"}, "chapters": {"45": "Polynomials"}}',
        )
        parser.add_argument("--limit", type=int, default=None, help="Import at most N questions (testing).")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and convert everything but write nothing to the DB.",
        )
        parser.add_argument(
            "--report-unknowns",
            action="store_true",
            help=(
                "Read-only scan: walk every {{...}} token across all subparts, "
                "report identifiers not declared as sampled variables and not in "
                "the croupier allowlist (_SAFE_CONSTS / _SAFE_FUNCS), then exit. "
                "Writes nothing to the DB."
            ),
        )

    def handle(self, *args, **options):
        source = Path(options["source"])
        containers_dir = source / "containers"
        raw_dir = source / "raw"
        if not containers_dir.is_dir() or not raw_dir.is_dir():
            raise CommandError(f"Expected 'containers' and 'raw' subdirs under {source}")

        mapping = self._load_mapping(options.get("mapping"))
        limit = options.get("limit")
        dry_run = options.get("dry_run", False)

        if options.get("report_unknowns"):
            self._report_unknowns(containers_dir, raw_dir, limit)
            return

        stats = {"imported": 0, "updated": 0, "skipped": 0, "subjects": 0, "chapters": 0, "images": 0}
        container_files = sorted(containers_dir.rglob("*.json"))

        if dry_run:
            # One outer transaction rolled back at the end: taxonomy created during
            # the dry run stays valid for FK references but never persists.
            with transaction.atomic():
                self._import_all(container_files, raw_dir, mapping, stats, limit)
                transaction.set_rollback(True)
        else:
            self._import_all(container_files, raw_dir, mapping, stats, limit)

        self._report(stats, dry_run)

    def _import_all(self, container_files, raw_dir, mapping, stats, limit) -> None:
        for container_path in container_files:
            if limit is not None and (stats["imported"] + stats["updated"]) >= limit:
                break
            try:
                # Nested atomic = savepoint when inside the dry-run transaction, so
                # one malformed question rolls back only itself, not the whole run.
                with transaction.atomic():
                    result = self._import_container(container_path, raw_dir, mapping, stats)
                stats[result] += 1
            except Exception as exc:  # noqa: BLE001 — one bad question must not abort the import
                stats["skipped"] += 1
                self.stderr.write(self.style.WARNING(f"skip {container_path.name}: {exc}"))

    # ── helpers ──────────────────────────────────────────────────────────────

    def _load_mapping(self, path: str | None) -> dict:
        """Load the ID→name mapping.

        With ``--mapping`` the given file is used as-is. Without it, the bundled
        curated ``data/cabinet_taxonomy.json`` is used by default so a plain
        import names subjects/chapters properly instead of leaving
        ``Imported Subject/Chapter N`` placeholders. Chapter keys may be either
        the composite ``"<standard>:<subject_id>:<chapter_id>"`` form (preferred —
        cabinet chapter_ids are reused across standards/subjects) or a flat
        ``"<chapter_id>"`` (legacy / test fixtures); both are honoured.
        """
        source: "str | Path | None" = path
        if source is None and _DEFAULT_TAXONOMY_PATH.is_file():
            source = _DEFAULT_TAXONOMY_PATH
        if source is None:
            return {"subjects": {}, "chapters": {}}
        with open(source, encoding="utf-8") as fh:
            data = json.load(fh)
        return {"subjects": data.get("subjects", {}), "chapters": data.get("chapters", {})}

    def _parse_path_ids(self, container_path: Path, raw_root: Path) -> dict:
        """
        Path layout: .../containers/<board>/<school>/<standard>/<subject_id>/<chapter_id>/<qid>.json
        Returns the legacy IDs needed to resolve taxonomy + locate raw subparts.
        """
        parts = container_path.parts
        # The last 6 parts are board, school, standard, subject_id, chapter_id, <qid>.json
        board, school, standard, subject_id, chapter_id, qfile = parts[-6:]
        return {
            "board": board,
            "school": school,
            "standard": int(standard),
            "subject_id": subject_id,
            "chapter_id": chapter_id,
            "question_id": qfile.removesuffix(".json"),
            "raw_dir": raw_root / board / school / standard / subject_id / chapter_id,
        }

    def _resolve_taxonomy(self, ids: dict, mapping: dict, stats: dict):
        standard, _ = Standard.objects.get_or_create(number=ids["standard"])

        subject_name = mapping["subjects"].get(str(ids["subject_id"]), f"Imported Subject {ids['subject_id']}")
        subject, s_created = Subject.objects.get_or_create(name=subject_name)
        if s_created:
            stats["subjects"] += 1

        # Chapter ids are reused across standards/subjects (e.g. chapter 44 is
        # Physics-Thermo for subject 3 but Chemistry-Thermo for subject 4), so
        # prefer the composite key; fall back to the flat chapter_id, then to a
        # placeholder.
        chapters = mapping["chapters"]
        composite_key = f"{ids['standard']}:{ids['subject_id']}:{ids['chapter_id']}"
        chapter_name = (
            chapters.get(composite_key)
            or chapters.get(str(ids["chapter_id"]))
            or f"Imported Chapter {ids['chapter_id']}"
        )
        chapter, c_created = Chapter.objects.get_or_create(subject=subject, standard=standard, name=chapter_name)
        if c_created:
            stats["chapters"] += 1

        return standard, subject, chapter

    def _import_container(self, container_path: Path, raw_root: Path, mapping: dict, stats: dict) -> str:
        ids = self._parse_path_ids(container_path, raw_root)
        with open(container_path, encoding="utf-8") as fh:
            container = json.load(fh)

        subpart_ids = container.get("subparts") or []
        if not subpart_ids:
            raise ValueError("container has no subparts")

        # Raw URL prefix up to this chapter's directory (M7-06 inline images).
        chapter_base = (
            f"{_CABINET_RAW_BASE}/{ids['board']}/{ids['school']}/{ids['standard']}/"
            f"{ids['subject_id']}/{ids['chapter_id']}"
        )

        converted = []
        for index, sp_id in enumerate(subpart_ids):
            sp_path = ids["raw_dir"] / f"{sp_id}.json"
            with open(sp_path, encoding="utf-8") as fh:
                fields = convert_subpart(json.load(fh), index)

            # M7-06: rewrite inline image references (`#{name}#` tokens / relative
            # `<img src>`) embedded in the HTML body to absolute raw-GitHub URLs.
            for field in ("question_text", "solution_text", "hint_text"):
                rewritten = rewrite_inline_images(fields.get(field, ""), ids["raw_dir"], chapter_base)
                if rewritten != fields.get(field, ""):
                    stats["inline_images"] = stats.get("inline_images", 0) + 1
                fields[field] = rewritten

            # M7-11: resolve #{img}# tokens inside the preserved interactive HTML
            # to BARE URLs (they sit inside JS/attribute contexts, not prose).
            if fields.get("is_interactive"):
                fields["interactive_html"] = resolve_inline_image_urls(
                    fields.get("interactive_html", ""), ids["raw_dir"], chapter_base
                )
                stats["interactive"] = stats.get("interactive", 0) + 1

            # Image discovery — attach a raw.githubusercontent.com URL if a
            # matching image file lives in the chapter's raw directory (either
            # as a sibling of the JSON or under an `img/` subdirectory).
            found = _find_subpart_image(ids["raw_dir"], sp_id)
            if found:
                rel_path, _ext = found
                fields["image_url"] = f"{chapter_base}/{rel_path}"
                stats["images"] = stats.get("images", 0) + 1

            converted.append(fields)

        # M7-03: the question summary type is the unanimous subpart type, or
        # "compound" when the subparts are heterogeneous.
        subpart_types = {f["_question_type"].value for f in converted}
        if len(subpart_types) == 1:
            q_type = next(iter(subpart_types))
        else:
            q_type = QuestionType.COMPOUND.value
            stats["compound"] = stats.get("compound", 0) + 1
        standard, subject, chapter = self._resolve_taxonomy(ids, mapping, stats)

        # Stem extraction. Priority:
        #   1. Container-level `content.text` (+ optional `content.img`) — the
        #      cabinet's *authoritative* question prompt for compound questions
        #      whose subparts are sub-questions ("Graph 1", "Graph 2", "Graph 3"
        #      under "For the given graphs find the number of zeros in each
        #      case"). 38% of containers carry this field; without lifting it,
        #      students see only the sub-labels and not the actual question.
        #   2. Fallback: subparts that share an identical leading paragraph
        #      (M7-07). Used when the container has no explicit content.
        container_content = container.get("content") or {}
        container_stem = ""
        if isinstance(container_content, dict):
            raw_stem = (container_content.get("text") or "").strip()
            if raw_stem:
                # Rewrite inline images and resolve `#{name}#` tokens in the
                # stem just like we do for subpart bodies (M7-06).
                container_stem = rewrite_inline_images(raw_stem, ids["raw_dir"], chapter_base)
            # Container can also carry its own diagram (content.img) — render
            # it as a trailing <img> in the stem so the picture stays attached
            # to the question prompt, not orphaned on a subpart.
            container_img = container_content.get("img")
            if container_img:
                img_url = (
                    container_img
                    if str(container_img).startswith(("http://", "https://"))
                    else f"{chapter_base}/img/{container_img}"
                )
                img_tag = f'<p><img src="{img_url}" alt=""></p>'
                container_stem = (container_stem + img_tag).strip() if container_stem else img_tag

        if container_stem:
            stem_text = container_stem
        else:
            stem_text = _lift_shared_stem(converted) if len(converted) > 1 else ""
        if stem_text:
            stats["stems"] = stats.get("stems", 0) + 1

        # M7-05: the cabinet tag must be unique per *imported* question, not per
        # raw cabinet question_id. Several chapters share the same numeric
        # question_id (1.json appears in dozens of chapter folders), so the
        # legacy `cabinet:<id>` tag collapsed 33 distinct questions into one.
        # Scope the tag by chapter PK to restore identity.
        cabinet_tag, _ = QuestionTag.objects.get_or_create(
            name=f"cabinet:c{chapter.id}:q{ids['question_id']}",
            defaults={"tag_type": "special"},
        )

        existing = Question.objects.filter(tags=cabinet_tag).first()
        status = "updated" if existing else "imported"

        question = existing or Question(standard=standard, subject=subject, chapter=chapter, question_type=q_type)
        question.standard = standard
        question.subject = subject
        question.chapter = chapter
        question.question_type = q_type
        question.stem_text = stem_text
        question.save()
        question.tags.add(cabinet_tag)

        # Replace subparts wholesale so re-imports stay in sync with the source.
        question.subparts.all().delete()
        for fields in converted:
            fields.pop("_question_type", None)
            QuestionSubpart.objects.create(question=question, **fields)

        return status

    def _report_unknowns(self, containers_dir: Path, raw_root: Path, limit: int | None) -> None:
        """M7-08: scan every cabinet token expression, surface un-allowlisted names.

        Read-only, no DB writes. Skips containers that fail to parse — the
        regular import already reports those as conversion errors.
        """
        counts: Counter[str] = Counter()
        examples: dict[str, str] = {}
        scanned = 0
        skipped = 0

        container_files = sorted(containers_dir.rglob("*.json"))
        for container_path in container_files:
            if limit is not None and scanned >= limit:
                break
            try:
                ids = self._parse_path_ids(container_path, raw_root)
                with open(container_path, encoding="utf-8") as fh:
                    container = json.load(fh)
                for index, sp_id in enumerate(container.get("subparts") or []):
                    sp_path = ids["raw_dir"] / f"{sp_id}.json"
                    with open(sp_path, encoding="utf-8") as fh:
                        fields = convert_subpart(json.load(fh), index)
                    declared = set((fields.get("variable_constraints") or {}).keys())
                    for expr in _iter_expressions(fields):
                        for name in _collect_unknown_names(expr, declared):
                            counts[name] += 1
                            examples.setdefault(name, expr)
                scanned += 1
            except Exception as exc:  # noqa: BLE001 — same tolerance as the import path
                skipped += 1
                self.stderr.write(self.style.WARNING(f"skip {container_path.name}: {exc}"))

        self.stdout.write(f"scanned containers: {scanned}  skipped: {skipped}")
        if not counts:
            self.stdout.write(self.style.SUCCESS("no unknown identifiers — every token resolves."))
            return

        self.stdout.write(self.style.WARNING(f"unknown identifiers ({len(counts)} distinct):"))
        # Sort by frequency desc, then name asc so the worst offenders surface first.
        for name, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
            self.stdout.write(f"  {name:<24} {count:>6}   e.g. {{{{ {examples[name]} }}}}")
        self.stdout.write(f"total occurrences: {sum(counts.values())}")

    def _report(self, stats: dict, dry_run: bool) -> None:
        prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}imported={stats['imported']} updated={stats['updated']} "
                f"skipped={stats['skipped']} "
                f"new_subjects={stats['subjects']} new_chapters={stats['chapters']} "
                f"images={stats.get('images', 0)} stems={stats.get('stems', 0)} "
                f"inline_images={stats.get('inline_images', 0)} compound={stats.get('compound', 0)} "
                f"interactive={stats.get('interactive', 0)}"
            )
        )
