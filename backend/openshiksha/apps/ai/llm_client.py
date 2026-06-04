"""
LLM client for AI-generated explanations.

Provider cascade (first available wins):
  1. Anthropic Claude     — set ANTHROPIC_API_KEY
  2. Google AI Studio     — set GOOGLE_AI_API_KEY (free tier)
                            override model with GOOGLE_AI_MODEL (default gemini-2.5-flash)
  3. Ollama (local)       — set OLLAMA_BASE_URL, or run Ollama at localhost:11434
                            override model with OLLAMA_MODEL (default gemma3:4b)
  4. Stub                 — plain text fallback for dev/test with no keys

Free-tier model note (as of 2026-06):
  - ``gemini-2.5-flash`` works on Google AI Studio's free tier with generous
    daily quota — this is the safe default.
  - ``gemini-2.0-flash`` requires billing even though the docs imply otherwise;
    a brand-new free-tier key returns ``RESOURCE_EXHAUSTED`` on the first call.
  - The previous default ``gemma-4-it`` does **not exist** as a model name —
    the real Gemma 4 models on AI Studio are ``gemma-4-26b-a4b-it`` and
    ``gemma-4-31b-it`` (slower and less reliable than Gemini Flash for our
    use cases).

Grade calibration tiers:
  1–6  (primary):  very simple words, short sentences, real-world analogies
  7–9  (middle):   clear language, explains the concept and the mistake
  10–12 (senior):  subject-specific terms allowed, concise

Language support:
  en — English (default)
  hi — Hindi (LLM prompted to respond in Hindi)
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

CLAUDE_MODEL = "claude-sonnet-4-6"
# Google AI Studio default. Env-overridable via GOOGLE_AI_MODEL so a deployment
# can pin to a different free-tier-eligible Gemini/Gemma model without code
# changes. The default must work on the AI Studio free tier with no billing.
GOOGLE_AI_DEFAULT_MODEL = "gemini-2.5-flash"
# Local Ollama default. Env-overridable via OLLAMA_MODEL.
OLLAMA_DEFAULT_MODEL = "gemma3:4b"
OLLAMA_DEFAULT_URL = "http://localhost:11434"
MAX_TOKENS = 300


def _google_ai_model() -> str:
    return os.environ.get("GOOGLE_AI_MODEL", "") or GOOGLE_AI_DEFAULT_MODEL


def _ollama_model() -> str:
    return os.environ.get("OLLAMA_MODEL", "") or OLLAMA_DEFAULT_MODEL


# ─────────────────────────────────────────────────────────────
# Prompt building (shared across all providers)
# ─────────────────────────────────────────────────────────────


def _grade_tier(grade_level: int) -> str:
    if grade_level <= 6:
        return "primary school (grades 1–6). Use very simple words, short sentences, and real-life examples."
    if grade_level <= 9:
        return "middle school (grades 7–9). Use clear language and explain the concept behind the answer."
    return "high school (grades 10–12). You may use subject-specific terms but keep the explanation concise."


def _build_prompt(
    question_text: str,
    options: list[dict] | None,
    student_answer: Any,
    correct_answer: dict,
    is_correct: bool,
    grade_level: int,
    language: str,
) -> str:
    correct_value = correct_answer.get("answer", "")

    if options:
        key_to_text = {opt["key"]: opt["text"] for opt in options if "key" in opt and "text" in opt}
        correct_option_text = key_to_text.get(str(correct_value), str(correct_value))
        student_option_text = key_to_text.get(str(student_answer), str(student_answer))
    else:
        correct_option_text = str(correct_value)
        student_option_text = str(student_answer)

    outcome = "correctly answered" if is_correct else "answered incorrectly"
    tier = _grade_tier(grade_level)
    lang_instruction = "\n\nRespond in Hindi (Devanagari script)." if language == "hi" else ""

    correct_line = (
        "- Tells the student WHY their answer is correct and reinforces the key concept."
        if is_correct
        else "- Tells the student WHY their answer was wrong and what the correct reasoning is."
    )

    return (
        f"You are a helpful tutor for a student in {tier}\n\n"
        f"A student {outcome} the following question:\n\n"
        f"Question: {question_text}\n\n"
        f"Student's answer: {student_option_text}\n"
        f"Correct answer: {correct_option_text}\n\n"
        f"Write a brief explanation (2–4 sentences) that:\n"
        f"{correct_line}\n"
        f"- Is encouraging and supportive in tone.\n"
        f"- Does NOT just restate the question or the answers.\n"
        f"- Uses language appropriate for {tier}"
        f"{lang_instruction}\n\n"
        f"Explanation:"
    )


# ─────────────────────────────────────────────────────────────
# Provider implementations
# ─────────────────────────────────────────────────────────────


def _call_anthropic(prompt: str, api_key: str) -> dict:
    import anthropic
    from anthropic.types import TextBlock

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    text_blocks = [b for b in message.content if isinstance(b, TextBlock)]
    text = text_blocks[0].text.strip() if text_blocks else ""
    return {
        "text": text,
        "model": message.model,
        "input_tokens": message.usage.input_tokens,
        "output_tokens": message.usage.output_tokens,
    }


def _call_google_ai_studio(prompt: str, api_key: str) -> dict:
    """Call a Google AI Studio model (default: gemini-2.5-flash, free tier).

    Reads the active model from GOOGLE_AI_MODEL env var (or the default).
    Works for both Gemini and Gemma family — same SDK, same endpoint.
    """
    from google import genai
    from google.genai import types

    model = _google_ai_model()
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=MAX_TOKENS,
            temperature=0.7,
        ),
    )
    text = response.text.strip() if response.text else ""
    # Google AI SDK returns usage metadata on the response
    usage = getattr(response, "usage_metadata", None)
    input_tokens = getattr(usage, "prompt_token_count", 0) or 0
    output_tokens = getattr(usage, "candidates_token_count", 0) or 0
    return {
        "text": text,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }


def _call_ollama(prompt: str, base_url: str) -> dict:
    """Call a local Ollama instance (on-device, zero cost)."""
    import httpx

    model = _ollama_model()
    url = f"{base_url.rstrip('/')}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": MAX_TOKENS, "temperature": 0.7},
    }
    resp = httpx.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    text = data.get("response", "").strip()
    return {
        "text": text,
        "model": f"ollama/{model}",
        "input_tokens": data.get("prompt_eval_count", 0),
        "output_tokens": data.get("eval_count", 0),
    }


def _ollama_reachable(base_url: str) -> bool:
    """Quick health-check — returns True if Ollama is up."""
    import httpx

    try:
        resp = httpx.get(f"{base_url.rstrip('/')}/api/tags", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────


def generate_explanation(
    question_text: str,
    options: list[dict] | None,
    student_answer: Any,
    correct_answer: dict,
    is_correct: bool,
    grade_level: int,
    language: str = "en",
) -> dict:
    """
    Generate a plain-language explanation for a student answer.

    Provider cascade (first available wins):
      1. Anthropic Claude  — ANTHROPIC_API_KEY env var
      2. Google AI Studio    — GOOGLE_AI_API_KEY env var (free tier)
      3. Ollama (local)    — OLLAMA_BASE_URL env var, or localhost:11434
      4. Stub              — plain text, no LLM call

    Returns:
        {"text": str, "model": str, "input_tokens": int, "output_tokens": int}
    """
    prompt = _build_prompt(
        question_text=question_text,
        options=options,
        student_answer=student_answer,
        correct_answer=correct_answer,
        is_correct=is_correct,
        grade_level=grade_level,
        language=language,
    )

    # 1. Anthropic Claude
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if anthropic_key:
        try:
            logger.debug("generate_explanation: using Anthropic Claude")
            return _call_anthropic(prompt, anthropic_key)
        except Exception:
            logger.exception("generate_explanation: Anthropic call failed, trying next provider")

    # 2. Google AI Studio (free tier via Google AI Studio)
    google_key = os.environ.get("GOOGLE_AI_API_KEY", "")
    if google_key:
        try:
            logger.debug("generate_explanation: using Google AI Studio")
            return _call_google_ai_studio(prompt, google_key)
        except Exception:
            logger.exception("generate_explanation: Google AI Studio call failed, trying next provider")

    # 3. Ollama (on-device, zero cost)
    ollama_url = os.environ.get("OLLAMA_BASE_URL", OLLAMA_DEFAULT_URL)
    if _ollama_reachable(ollama_url):
        try:
            logger.debug("generate_explanation: using Ollama at %s", ollama_url)
            return _call_ollama(prompt, ollama_url)
        except Exception:
            logger.exception("generate_explanation: Ollama call failed, falling back to stub")

    # 4. Stub
    logger.warning(
        "generate_explanation: no LLM provider available — returning stub. "
        "Set ANTHROPIC_API_KEY, GOOGLE_AI_API_KEY, or run Ollama at %s",
        ollama_url,
    )
    return {
        "text": _stub_explanation(is_correct),
        "model": "stub",
        "input_tokens": 0,
        "output_tokens": 0,
    }


def _stub_explanation(is_correct: bool) -> str:
    if is_correct:
        return "Great job! Your answer is correct. Keep up the good work."
    return "That answer was incorrect. Review the concept and try again."


# ─────────────────────────────────────────────────────────────
# Question Generation
# ─────────────────────────────────────────────────────────────

QUESTION_GEN_MAX_TOKENS = 2500

_QUESTION_GEN_TOOL = {
    "name": "save_questions",
    "description": "Save the generated questions in structured JSON format.",
    "input_schema": {
        "type": "object",
        "required": ["questions"],
        "properties": {
            "questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["question_text", "correct_answer"],
                    "properties": {
                        "question_text": {"type": "string"},
                        "options": {
                            "type": ["array", "null"],
                            "items": {
                                "type": "object",
                                "properties": {
                                    "key": {"type": "string"},
                                    "text": {"type": "string"},
                                },
                            },
                        },
                        "correct_answer": {"type": "string"},
                        "variable_constraints": {
                            "type": ["object", "null"],
                            "additionalProperties": {
                                "type": "object",
                                "properties": {
                                    "min": {"type": "number"},
                                    "max": {"type": "number"},
                                    "integer": {"type": "boolean"},
                                },
                            },
                        },
                        "suggested_tags": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "solution": {"type": "string"},
                    },
                },
            }
        },
    },
}


def _build_question_gen_prompt(
    topic: str,
    chapter_name: str,
    subject_name: str,
    standard_number: int,
    question_type: str,
    difficulty: int,
    count: int,
) -> str:
    type_instructions = {
        "mcq": (
            "Multiple choice with exactly 4 options keyed A, B, C, D. "
            "Exactly one correct answer. Put all 4 options in the 'options' array."
        ),
        "multi_select": (
            "Multi-select with 4 options keyed A, B, C, D — 2 or more are correct. "
            "Set correct_answer to a comma-separated string like 'A,C'. "
            "Put all 4 options in the 'options' array."
        ),
        "numeric": (
            "Numeric answer question — the answer is a number. "
            "You may use {{variable}} tokens (double curly braces) for parameterization "
            "and provide variable_constraints for each token. "
            "Set correct_answer to the numeric value or expression string."
        ),
        "fill_blank": (
            "Fill in the blank. The answer is a short word or phrase. "
            "Set correct_answer to the expected answer string. "
            "Leave options as null."
        ),
    }
    type_hint = type_instructions.get(question_type, type_instructions["mcq"])
    _diff_labels = {1: "very easy", 2: "easy", 3: "medium", 4: "hard", 5: "very hard"}
    difficulty_label = _diff_labels.get(difficulty, "medium")

    return (
        f"Generate exactly {count} {difficulty_label} difficulty question(s) "
        f"about '{topic}' for Standard {standard_number} {subject_name}, "
        f"chapter '{chapter_name}' — Indian K-12 curriculum (CBSE/ICSE style).\n\n"
        f"Question type: {type_hint}\n\n"
        f"Guidelines:\n"
        f"- Each question should test a distinct concept or sub-topic.\n"
        f"- Use LaTeX for math ($expression$ inline, $$expression$$ display).\n"
        f"- For numeric/fill_blank, use {{{{variable}}}} tokens for parameterization "
        f"and include variable_constraints (min, max, integer: true/false).\n"
        f"- suggested_tags: 1–3 short concept keywords (e.g. 'polynomials', 'factoring').\n"
        f"- solution: a concise step-by-step worked solution (2–4 steps, LaTeX allowed) "
        f"showing how to arrive at the correct answer.\n"
        f"- Difficulty {difficulty}/5: "
        + (
            "focus on direct recall and definitions."
            if difficulty <= 2
            else (
                "test application and multi-step reasoning."
                if difficulty <= 3
                else "require analysis, synthesis, and non-obvious connections."
            )
        )
        + "\n\n"
        "Call save_questions with the structured result."
    )


def _call_anthropic_generate_questions(prompt: str, api_key: str) -> list[dict]:
    import anthropic
    from anthropic.types import ToolChoiceAnyParam, ToolParam, ToolUseBlock

    client = anthropic.Anthropic(api_key=api_key)
    tool: ToolParam = {
        "name": str(_QUESTION_GEN_TOOL["name"]),
        "description": str(_QUESTION_GEN_TOOL["description"]),
        "input_schema": _QUESTION_GEN_TOOL["input_schema"],  # type: ignore[typeddict-item]
    }
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=QUESTION_GEN_MAX_TOKENS,
        tools=[tool],
        tool_choice=ToolChoiceAnyParam(type="any"),
        messages=[{"role": "user", "content": prompt}],
    )
    for block in message.content:
        if isinstance(block, ToolUseBlock) and block.name == "save_questions":
            input_data = block.input if isinstance(block.input, dict) else {}
            questions = input_data.get("questions", [])
            return questions if isinstance(questions, list) else []
    return []


def _call_google_generate_questions(prompt: str, api_key: str) -> list[dict]:
    """Fallback: ask the Google AI Studio model to return JSON and parse it."""
    import json as _json

    from google import genai
    from google.genai import types

    json_prompt = (
        prompt + "\n\nIMPORTANT: Respond ONLY with a valid JSON array of question objects, "
        'no markdown fences, no explanation. Example: [{"question_text": "...", ...}]'
    )
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=_google_ai_model(),
        contents=json_prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=QUESTION_GEN_MAX_TOKENS,
            temperature=0.8,
        ),
    )
    text = (response.text or "").strip()
    text = text.lstrip("```json").lstrip("```").rstrip("```").strip()
    return _json.loads(text)


def _call_ollama_generate_questions(prompt: str, base_url: str) -> list[dict]:
    import json as _json

    import httpx

    json_prompt = prompt + "\n\nIMPORTANT: Respond ONLY with a valid JSON array of question objects."
    payload = {
        "model": _ollama_model(),
        "prompt": json_prompt,
        "stream": False,
        "options": {"num_predict": QUESTION_GEN_MAX_TOKENS, "temperature": 0.8},
    }
    resp = httpx.post(f"{base_url.rstrip('/')}/api/generate", json=payload, timeout=120)
    resp.raise_for_status()
    text = resp.json().get("response", "").strip()
    text = text.lstrip("```json").lstrip("```").rstrip("```").strip()
    return _json.loads(text)


def _stub_questions(question_type: str, count: int) -> list[dict]:
    stubs = []
    for i in range(count):
        q: dict = {
            "question_text": f"Sample {question_type} question {i + 1} (AI provider unavailable)",
            "correct_answer": "A" if question_type in ("mcq", "multi_select") else "42",
            "variable_constraints": None,
            "suggested_tags": ["sample"],
            "solution": "",
        }
        if question_type in ("mcq", "multi_select"):
            q["options"] = [
                {"key": "A", "text": "Option A"},
                {"key": "B", "text": "Option B"},
                {"key": "C", "text": "Option C"},
                {"key": "D", "text": "Option D"},
            ]
        else:
            q["options"] = None
        stubs.append(q)
    return stubs


def generate_questions(
    topic: str,
    chapter_name: str,
    subject_name: str,
    standard_number: int,
    question_type: str,
    difficulty: int,
    count: int,
) -> list[dict]:
    """
    Generate question drafts using the same LLM cascade as generate_explanation.

    Returns a list of draft dicts:
        [{question_text, options, correct_answer, variable_constraints, suggested_tags}]
    """
    prompt = _build_question_gen_prompt(
        topic=topic,
        chapter_name=chapter_name,
        subject_name=subject_name,
        standard_number=standard_number,
        question_type=question_type,
        difficulty=difficulty,
        count=count,
    )

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if anthropic_key:
        try:
            logger.debug("generate_questions: using Anthropic Claude")
            return _call_anthropic_generate_questions(prompt, anthropic_key)
        except Exception:
            logger.exception("generate_questions: Anthropic failed, trying next provider")

    google_key = os.environ.get("GOOGLE_AI_API_KEY", "")
    if google_key:
        try:
            logger.debug("generate_questions: using Google AI Studio")
            return _call_google_generate_questions(prompt, google_key)
        except Exception:
            logger.exception("generate_questions: Google AI Studio call failed, trying next provider")

    ollama_url = os.environ.get("OLLAMA_BASE_URL", OLLAMA_DEFAULT_URL)
    if _ollama_reachable(ollama_url):
        try:
            logger.debug("generate_questions: using Ollama at %s", ollama_url)
            return _call_ollama_generate_questions(prompt, ollama_url)
        except Exception:
            logger.exception("generate_questions: Ollama failed, falling back to stub")

    logger.warning("generate_questions: no LLM provider available — returning stub")
    return _stub_questions(question_type, count)


# ─────────────────────────────────────────────────────────────
# Weekly Class Summary (Teacher AI Assistant)
# ─────────────────────────────────────────────────────────────

CLASS_SUMMARY_MAX_TOKENS = 400


def _build_class_summary_prompt(stats: dict, subject_name: str, standard_number: int) -> str:
    def _chapter_list(chapters: list[dict]) -> str:
        if not chapters:
            return "none"
        return "; ".join(f"{c['chapter_name']} ({c['avg_score']:.0%})" for c in chapters)

    return (
        f"You are an assistant writing a weekly progress note for a school teacher "
        f"of Standard {standard_number} {subject_name}.\n\n"
        f"This week's data for the class:\n"
        f"- Students enrolled: {stats['total_students']}\n"
        f"- Students who practised: {stats['active_students']}\n"
        f"- Questions attempted: {stats['ticks_recorded']}\n"
        f"- Class average score: {stats['class_avg_score']:.0%}\n"
        f"- Chapters the class struggled with: {_chapter_list(stats['struggling_chapters'])}\n"
        f"- Chapters the class did well in: {_chapter_list(stats['strong_chapters'])}\n\n"
        f"Write a short report (3–5 sentences) for the teacher that:\n"
        f"- Opens with participation and overall performance.\n"
        f"- Names the specific chapters to celebrate and the ones needing reteaching.\n"
        f"- Ends with one concrete, actionable suggestion for next week.\n"
        f"- Uses a warm, professional tone. Do NOT use markdown or bullet points.\n\n"
        f"Report:"
    )


def _stub_class_summary(stats: dict) -> str:
    parts = [
        f"{stats['active_students']} of {stats['total_students']} students practised this week, "
        f"attempting {stats['ticks_recorded']} questions at a {stats['class_avg_score']:.0%} class average."
    ]
    if stats["strong_chapters"]:
        names = ", ".join(c["chapter_name"] for c in stats["strong_chapters"])
        parts.append(f"The class is doing well in {names}.")
    if stats["struggling_chapters"]:
        names = ", ".join(c["chapter_name"] for c in stats["struggling_chapters"])
        parts.append(f"Consider revisiting {names}, where scores are lowest.")
    return " ".join(parts)


def _call_anthropic_text(prompt: str, api_key: str, max_tokens: int) -> dict:
    import anthropic
    from anthropic.types import TextBlock

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    text_blocks = [b for b in message.content if isinstance(b, TextBlock)]
    text = text_blocks[0].text.strip() if text_blocks else ""
    return {
        "text": text,
        "model": message.model,
        "input_tokens": message.usage.input_tokens,
        "output_tokens": message.usage.output_tokens,
    }


def generate_class_summary(
    stats: dict,
    subject_name: str,
    standard_number: int,
) -> dict:
    """
    Generate a plain-language weekly class summary for a teacher.

    Uses the same provider cascade as generate_explanation. Always returns a
    usable narrative — the stub composes a deterministic sentence from the stats
    when no LLM provider is available.

    Returns:
        {"text": str, "model": str, "input_tokens": int, "output_tokens": int}
    """
    prompt = _build_class_summary_prompt(stats, subject_name, standard_number)

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if anthropic_key:
        try:
            logger.debug("generate_class_summary: using Anthropic Claude")
            return _call_anthropic_text(prompt, anthropic_key, CLASS_SUMMARY_MAX_TOKENS)
        except Exception:
            logger.exception("generate_class_summary: Anthropic failed, trying next provider")

    google_key = os.environ.get("GOOGLE_AI_API_KEY", "")
    if google_key:
        try:
            logger.debug("generate_class_summary: using Google AI Studio")
            return _call_google_ai_studio(prompt, google_key)
        except Exception:
            logger.exception("generate_class_summary: Google AI Studio call failed, trying next provider")

    ollama_url = os.environ.get("OLLAMA_BASE_URL", OLLAMA_DEFAULT_URL)
    if _ollama_reachable(ollama_url):
        try:
            logger.debug("generate_class_summary: using Ollama at %s", ollama_url)
            return _call_ollama(prompt, ollama_url)
        except Exception:
            logger.exception("generate_class_summary: Ollama failed, falling back to stub")

    logger.warning("generate_class_summary: no LLM provider available — returning stub")
    return {
        "text": _stub_class_summary(stats),
        "model": "stub",
        "input_tokens": 0,
        "output_tokens": 0,
    }


# ─────────────────────────────────────────────────────────────
# Teacher AI Assistant — Assignment Draft Rationale
# ─────────────────────────────────────────────────────────────

DRAFT_RATIONALE_MAX_TOKENS = 250


def _build_draft_rationale_prompt(
    subject_name: str,
    standard_number: int,
    target_chapters: list[dict],
    question_count: int,
) -> str:
    chapters = (
        "; ".join(f"{c['chapter_name']} (class avg {c['avg_score']:.0%})" for c in target_chapters)
        if target_chapters
        else "none identified"
    )
    return (
        f"You are helping a school teacher of Standard {standard_number} {subject_name} "
        f"review an auto-generated practice assignment.\n\n"
        f"The assignment has {question_count} questions chosen to target the chapters "
        f"the class is currently weakest on: {chapters}.\n\n"
        f"Write a short note (2–4 sentences) for the teacher that:\n"
        f"- Explains which weaknesses this assignment is meant to address.\n"
        f"- Reassures them it focuses on recent struggle areas.\n"
        f"- Ends by inviting them to review and adjust before assigning.\n"
        f"- Uses a warm, professional tone. Do NOT use markdown or bullet points.\n\n"
        f"Note:"
    )


def _stub_draft_rationale(target_chapters: list[dict], question_count: int) -> str:
    if not target_chapters:
        return (
            f"This draft of {question_count} questions is ready for your review. "
            f"Adjust the selection as needed before assigning it to your class."
        )
    names = ", ".join(c["chapter_name"] for c in target_chapters)
    return (
        f"This draft gathers {question_count} questions focused on {names}, "
        f"the chapters your class has scored lowest on recently. "
        f"Review the selection and adjust it before assigning."
    )


def generate_draft_rationale(
    subject_name: str,
    standard_number: int,
    target_chapters: list[dict],
    question_count: int,
) -> dict:
    """
    Generate a plain-language rationale for an auto-drafted assignment.

    Uses the same provider cascade as the other generators and always returns a
    usable note — the stub composes a deterministic sentence from the targeted
    chapters when no LLM provider is configured.

    Returns:
        {"text": str, "model": str, "input_tokens": int, "output_tokens": int}
    """
    prompt = _build_draft_rationale_prompt(subject_name, standard_number, target_chapters, question_count)

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if anthropic_key:
        try:
            logger.debug("generate_draft_rationale: using Anthropic Claude")
            return _call_anthropic_text(prompt, anthropic_key, DRAFT_RATIONALE_MAX_TOKENS)
        except Exception:
            logger.exception("generate_draft_rationale: Anthropic failed, trying next provider")

    google_key = os.environ.get("GOOGLE_AI_API_KEY", "")
    if google_key:
        try:
            logger.debug("generate_draft_rationale: using Google AI Studio")
            return _call_google_ai_studio(prompt, google_key)
        except Exception:
            logger.exception("generate_draft_rationale: Google AI Studio call failed, trying next provider")

    ollama_url = os.environ.get("OLLAMA_BASE_URL", OLLAMA_DEFAULT_URL)
    if _ollama_reachable(ollama_url):
        try:
            logger.debug("generate_draft_rationale: using Ollama at %s", ollama_url)
            return _call_ollama(prompt, ollama_url)
        except Exception:
            logger.exception("generate_draft_rationale: Ollama failed, falling back to stub")

    logger.warning("generate_draft_rationale: no LLM provider available — returning stub")
    return {
        "text": _stub_draft_rationale(target_chapters, question_count),
        "model": "stub",
        "input_tokens": 0,
        "output_tokens": 0,
    }


# ─────────────────────────────────────────────────────────────
# Intelligent Hint System
# ─────────────────────────────────────────────────────────────

HINTS_MAX_TOKENS = 700
MISCONCEPTION_MAX_TOKENS = 400
DEFAULT_NUM_HINTS = 3

_HINTS_TOOL = {
    "name": "save_hints",
    "description": "Save the ordered list of progressive hints.",
    "input_schema": {
        "type": "object",
        "required": ["hints"],
        "properties": {
            "hints": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["level", "text"],
                    "properties": {
                        "level": {"type": "integer"},
                        "text": {"type": "string"},
                    },
                },
            }
        },
    },
}

_MISCONCEPTION_TOOL = {
    "name": "save_diagnosis",
    "description": "Save the structured misconception diagnosis.",
    "input_schema": {
        "type": "object",
        "required": ["misconception_label", "diagnosis", "remediation"],
        "properties": {
            "misconception_label": {"type": "string"},
            "diagnosis": {"type": "string"},
            "remediation": {"type": "string"},
        },
    },
}


def _answer_text(options: list[dict] | None, value: object) -> str:
    if options:
        key_to_text = {opt["key"]: opt["text"] for opt in options if "key" in opt and "text" in opt}
        return key_to_text.get(str(value), str(value))
    return str(value)


def _build_hints_prompt(
    question_text: str,
    options: list[dict] | None,
    correct_answer: dict,
    grade_level: int,
    num_hints: int,
) -> str:
    tier = _grade_tier(grade_level)
    options_block = ""
    if options:
        opts = "; ".join(f"{o.get('key')}) {o.get('text')}" for o in options)
        options_block = f"Options: {opts}\n"

    return (
        f"You are a patient tutor for a student in {tier}\n\n"
        f"A student is stuck on this question and has asked for help:\n\n"
        f"Question: {question_text}\n"
        f"{options_block}\n"
        f"Write exactly {num_hints} progressive hints that guide the student to "
        f"work out the answer THEMSELVES.\n"
        f"- Hint level 1 is a gentle nudge (point at the concept or first step).\n"
        f"- Each later hint is more concrete than the one before.\n"
        f"- The final hint may walk through the method but MUST NOT state the "
        f"final answer or which option is correct.\n"
        f"- Never reveal the answer. Never say 'the answer is ...'.\n"
        f"- Use language appropriate for {tier}\n"
        f"- Use LaTeX ($...$) for any math.\n\n"
        f"Call save_hints with the ordered list (level 1 first)."
    )


def _stub_hints(num_hints: int, static_hint: str = "") -> list[dict]:
    if static_hint:
        return [{"level": 1, "text": static_hint}]
    generic = [
        "Re-read the question carefully and underline exactly what is being asked.",
        "Identify which concept or formula from this chapter applies here.",
        "Write down what you know, then work step by step toward what you need.",
        "Check each step — a small slip early on often changes the final result.",
    ]
    return [{"level": i + 1, "text": generic[i % len(generic)]} for i in range(num_hints)]


def _parse_hints(raw: object, num_hints: int) -> list[dict]:
    """Normalise raw hint data into [{level, text}] with sequential levels."""
    items: list = []
    if isinstance(raw, dict):
        raw = raw.get("hints", [])
    if isinstance(raw, list):
        items = raw
    cleaned: list[dict] = []
    for i, item in enumerate(items):
        if isinstance(item, dict):
            text = str(item.get("text", "")).strip()
        else:
            text = str(item).strip()
        if text:
            cleaned.append({"level": len(cleaned) + 1, "text": text})
    return cleaned[:num_hints] if cleaned else _stub_hints(num_hints)


def _call_anthropic_tool(prompt: str, api_key: str, tool: dict, max_tokens: int) -> dict | None:
    import anthropic
    from anthropic.types import ToolChoiceAnyParam, ToolParam, ToolUseBlock

    client = anthropic.Anthropic(api_key=api_key)
    tool_param: ToolParam = {
        "name": str(tool["name"]),
        "description": str(tool["description"]),
        "input_schema": tool["input_schema"],
    }
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=max_tokens,
        tools=[tool_param],
        tool_choice=ToolChoiceAnyParam(type="any"),
        messages=[{"role": "user", "content": prompt}],
    )
    for block in message.content:
        if isinstance(block, ToolUseBlock) and block.name == tool["name"]:
            data = block.input if isinstance(block.input, dict) else {}
            return {
                "data": data,
                "model": message.model,
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
            }
    return None


def generate_hint_sequence(
    question_text: str,
    options: list[dict] | None,
    correct_answer: dict,
    grade_level: int = 8,
    num_hints: int = DEFAULT_NUM_HINTS,
    static_hint: str = "",
) -> dict:
    """
    Generate progressive hints for a question subpart.

    Uses the standard provider cascade. The stub falls back to the subpart's
    static ``hint_text`` when available, otherwise generic study prompts — so the
    result is always usable.

    Returns:
        {"hints": [{"level": int, "text": str}], "model": str,
         "input_tokens": int, "output_tokens": int}
    """
    prompt = _build_hints_prompt(question_text, options, correct_answer, grade_level, num_hints)

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if anthropic_key:
        try:
            result = _call_anthropic_tool(prompt, anthropic_key, _HINTS_TOOL, HINTS_MAX_TOKENS)
            if result:
                return {
                    "hints": _parse_hints(result["data"], num_hints),
                    "model": result["model"],
                    "input_tokens": result["input_tokens"],
                    "output_tokens": result["output_tokens"],
                }
        except Exception:
            logger.exception("generate_hint_sequence: Anthropic failed, trying next provider")

    google_key = os.environ.get("GOOGLE_AI_API_KEY", "")
    if google_key:
        try:
            import json as _json

            json_prompt = (
                prompt + "\n\nRespond ONLY with a JSON array like " '[{"level": 1, "text": "..."}], no markdown fences.'
            )
            res = _call_google_ai_studio(json_prompt, google_key)
            text = res["text"].lstrip("```json").lstrip("```").rstrip("```").strip()
            return {
                "hints": _parse_hints(_json.loads(text), num_hints),
                "model": res["model"],
                "input_tokens": res["input_tokens"],
                "output_tokens": res["output_tokens"],
            }
        except Exception:
            logger.exception("generate_hint_sequence: Google AI Studio call failed, trying next provider")

    ollama_url = os.environ.get("OLLAMA_BASE_URL", OLLAMA_DEFAULT_URL)
    if _ollama_reachable(ollama_url):
        try:
            import json as _json

            json_prompt = prompt + '\n\nRespond ONLY with a JSON array like [{"level": 1, "text": "..."}].'
            res = _call_ollama(json_prompt, ollama_url)
            text = res["text"].lstrip("```json").lstrip("```").rstrip("```").strip()
            return {
                "hints": _parse_hints(_json.loads(text), num_hints),
                "model": res["model"],
                "input_tokens": res["input_tokens"],
                "output_tokens": res["output_tokens"],
            }
        except Exception:
            logger.exception("generate_hint_sequence: Ollama failed, falling back to stub")

    logger.warning("generate_hint_sequence: no LLM provider available — returning stub")
    return {
        "hints": _stub_hints(num_hints, static_hint),
        "model": "stub",
        "input_tokens": 0,
        "output_tokens": 0,
    }


def _build_misconception_prompt(
    question_text: str,
    options: list[dict] | None,
    student_answer: object,
    correct_answer: dict,
    grade_level: int,
) -> str:
    tier = _grade_tier(grade_level)
    correct_value = correct_answer.get("answer", "")
    return (
        f"You are a diagnostic tutor for a student in {tier}\n\n"
        f"A student answered the following question INCORRECTLY:\n\n"
        f"Question: {question_text}\n"
        f"Student's answer: {_answer_text(options, student_answer)}\n"
        f"Correct answer: {_answer_text(options, correct_value)}\n\n"
        f"Diagnose the most likely misconception behind the wrong answer:\n"
        f"- misconception_label: a SHORT phrase (3–8 words) naming the faulty "
        f"idea (e.g. 'adds numerators and denominators').\n"
        f"- diagnosis: 1–2 sentences explaining the likely faulty reasoning.\n"
        f"- remediation: one concrete thing the student should review or practise.\n"
        f"- Be encouraging. Do not shame the student.\n\n"
        f"Call save_diagnosis with the result."
    )


def _stub_misconception() -> dict:
    return {
        "misconception_label": "needs review of this concept",
        "diagnosis": "The chosen answer suggests a gap in the underlying concept for this question.",
        "remediation": "Revisit the worked examples for this chapter and re-attempt a similar question.",
    }


def diagnose_misconception(
    question_text: str,
    options: list[dict] | None,
    student_answer: object,
    correct_answer: dict,
    grade_level: int = 8,
) -> dict:
    """
    Produce a structured misconception diagnosis for a wrong answer.

    Returns:
        {"misconception_label": str, "diagnosis": str, "remediation": str,
         "model": str, "input_tokens": int, "output_tokens": int}
    """
    prompt = _build_misconception_prompt(question_text, options, student_answer, correct_answer, grade_level)

    def _shape(data: dict, model: str, in_tok: int, out_tok: int) -> dict:
        return {
            "misconception_label": str(data.get("misconception_label", "")).strip()[:120]
            or _stub_misconception()["misconception_label"],
            "diagnosis": str(data.get("diagnosis", "")).strip() or _stub_misconception()["diagnosis"],
            "remediation": str(data.get("remediation", "")).strip(),
            "model": model,
            "input_tokens": in_tok,
            "output_tokens": out_tok,
        }

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if anthropic_key:
        try:
            result = _call_anthropic_tool(prompt, anthropic_key, _MISCONCEPTION_TOOL, MISCONCEPTION_MAX_TOKENS)
            if result:
                return _shape(result["data"], result["model"], result["input_tokens"], result["output_tokens"])
        except Exception:
            logger.exception("diagnose_misconception: Anthropic failed, trying next provider")

    google_key = os.environ.get("GOOGLE_AI_API_KEY", "")
    if google_key:
        try:
            import json as _json

            json_prompt = (
                prompt + "\n\nRespond ONLY with JSON: "
                '{"misconception_label": "...", "diagnosis": "...", "remediation": "..."}'
            )
            res = _call_google_ai_studio(json_prompt, google_key)
            text = res["text"].lstrip("```json").lstrip("```").rstrip("```").strip()
            return _shape(_json.loads(text), res["model"], res["input_tokens"], res["output_tokens"])
        except Exception:
            logger.exception("diagnose_misconception: Google AI Studio call failed, trying next provider")

    ollama_url = os.environ.get("OLLAMA_BASE_URL", OLLAMA_DEFAULT_URL)
    if _ollama_reachable(ollama_url):
        try:
            import json as _json

            json_prompt = (
                prompt + "\n\nRespond ONLY with JSON: "
                '{"misconception_label": "...", "diagnosis": "...", "remediation": "..."}'
            )
            res = _call_ollama(json_prompt, ollama_url)
            text = res["text"].lstrip("```json").lstrip("```").rstrip("```").strip()
            return _shape(_json.loads(text), res["model"], res["input_tokens"], res["output_tokens"])
        except Exception:
            logger.exception("diagnose_misconception: Ollama failed, falling back to stub")

    logger.warning("diagnose_misconception: no LLM provider available — returning stub")
    stub = _stub_misconception()
    return {**stub, "model": "stub", "input_tokens": 0, "output_tokens": 0}


# ─────────────────────────────────────────────────────────────
# Parent Intelligence Dashboard
# ─────────────────────────────────────────────────────────────

PARENT_SUMMARY_MAX_TOKENS = 450


def _build_parent_summary_prompt(stats: dict, language: str) -> str:
    def _chapter_list(chapters: list[dict]) -> str:
        if not chapters:
            return "none"
        return "; ".join(f"{c['chapter_name']} ({c['avg_score']:.0%})" for c in chapters)

    child_name = stats.get("child_name", "your child")
    grade_level = int(stats.get("grade_level", 8))
    subjects = ", ".join(stats.get("subjects_active", [])) or "no subjects this week"

    delta = stats.get("score_delta", 0.0)
    if delta > 0:
        trend_line = f"- Compared to last week: improved by {delta:.0%}."
    elif delta < 0:
        trend_line = f"- Compared to last week: dropped by {abs(delta):.0%}."
    else:
        trend_line = "- Compared to last week: roughly the same."

    lang_instruction = "\n\nRespond in Hindi (Devanagari script)." if language == "hi" else ""

    return (
        f"You are an assistant writing a weekly progress note for the PARENT of "
        f"a Grade {grade_level} student named {child_name}.\n\n"
        f"This week's data for the child:\n"
        f"- Days practised: {stats.get('active_days', 0)}\n"
        f"- Questions attempted: {stats.get('ticks_recorded', 0)}\n"
        f"- Subjects practised: {subjects}\n"
        f"- Average score: {stats.get('avg_score', 0.0):.0%}\n"
        f"{trend_line}\n"
        f"- Chapters where the child struggled: {_chapter_list(stats.get('weak_chapters', []))}\n"
        f"- Chapters where the child did well: {_chapter_list(stats.get('strong_chapters', []))}\n\n"
        f"Write a short note (3–5 sentences) for the parent that:\n"
        f"- Uses plain, friendly language a non-teacher parent will understand.\n"
        f"- Refers to the child by name.\n"
        f"- Opens with effort and overall trend (improving, steady, or slipping).\n"
        f"- Names one specific chapter to celebrate and one that needs attention.\n"
        f"- Ends with one concrete suggestion the parent can do at home this week.\n"
        f"- Do NOT use markdown or bullet points. Avoid jargon."
        f"{lang_instruction}\n\n"
        f"Note:"
    )


def _stub_parent_summary(stats: dict) -> str:
    name = stats.get("child_name", "Your child")
    ticks = stats.get("ticks_recorded", 0)
    if ticks == 0:
        return (
            f"{name} did not practise this week. A short daily routine — even 10 minutes — "
            f"makes a big difference. Encourage them to start with one easy chapter to build momentum."
        )

    parts = [
        f"{name} practised on {stats.get('active_days', 0)} day(s) this week, "
        f"attempting {ticks} questions at an average score of {stats.get('avg_score', 0.0):.0%}."
    ]
    delta = stats.get("score_delta", 0.0)
    if delta > 0.05:
        parts.append(f"That is up {delta:.0%} from last week — great momentum.")
    elif delta < -0.05:
        parts.append(f"That is down {abs(delta):.0%} from last week, so this week deserves a closer look.")

    if stats.get("strong_chapters"):
        names = ", ".join(c["chapter_name"] for c in stats["strong_chapters"])
        parts.append(f"{name} is doing well in {names}.")
    if stats.get("weak_chapters"):
        names = ", ".join(c["chapter_name"] for c in stats["weak_chapters"])
        parts.append(
            f"Spending 15 minutes on {names} together this week — even a few practice questions — would help a lot."
        )
    return " ".join(parts)


def generate_parent_summary(stats: dict, language: str = "en") -> dict:
    """
    Generate a plain-language weekly progress narrative for a parent about
    one child. Uses the same provider cascade as generate_class_summary.

    Always returns a usable narrative — the stub composes a deterministic note
    when no LLM provider is available.

    Returns:
        {"text": str, "model": str, "input_tokens": int, "output_tokens": int}
    """
    prompt = _build_parent_summary_prompt(stats, language)

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if anthropic_key:
        try:
            logger.debug("generate_parent_summary: using Anthropic Claude")
            return _call_anthropic_text(prompt, anthropic_key, PARENT_SUMMARY_MAX_TOKENS)
        except Exception:
            logger.exception("generate_parent_summary: Anthropic failed, trying next provider")

    google_key = os.environ.get("GOOGLE_AI_API_KEY", "")
    if google_key:
        try:
            logger.debug("generate_parent_summary: using Google AI Studio")
            return _call_google_ai_studio(prompt, google_key)
        except Exception:
            logger.exception("generate_parent_summary: Google AI Studio call failed, trying next provider")

    ollama_url = os.environ.get("OLLAMA_BASE_URL", OLLAMA_DEFAULT_URL)
    if _ollama_reachable(ollama_url):
        try:
            logger.debug("generate_parent_summary: using Ollama at %s", ollama_url)
            return _call_ollama(prompt, ollama_url)
        except Exception:
            logger.exception("generate_parent_summary: Ollama failed, falling back to stub")

    logger.warning("generate_parent_summary: no LLM provider available — returning stub")
    return {
        "text": _stub_parent_summary(stats),
        "model": "stub",
        "input_tokens": 0,
        "output_tokens": 0,
    }


# ─────────────────────────────────────────────────────────────
# Teacher AI Assistant — Open-Ended Response Grading
# ─────────────────────────────────────────────────────────────

OPEN_GRADE_MAX_TOKENS = 600

_OPEN_GRADE_TOOL = {
    "name": "save_grade",
    "description": "Save the suggested grade for a student's free-text answer.",
    "input_schema": {
        "type": "object",
        "required": ["score", "feedback", "confidence"],
        "properties": {
            "score": {
                "type": "number",
                "description": "Marks awarded, between 0 and the stated maximum.",
            },
            "feedback": {
                "type": "string",
                "description": "Brief, encouraging feedback for the student (2-4 sentences).",
            },
            "confidence": {
                "type": "number",
                "description": "Your confidence in this score from 0 to 1.",
            },
            "criterion_scores": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["label", "awarded", "max"],
                    "properties": {
                        "label": {"type": "string"},
                        "awarded": {"type": "number"},
                        "max": {"type": "number"},
                        "comment": {"type": "string"},
                    },
                },
            },
        },
    },
}


def _build_open_grade_prompt(
    question_text: str,
    model_answer: str,
    criteria: list[dict],
    response_text: str,
    max_marks: int,
    grade_level: int,
) -> str:
    tier = _grade_tier(grade_level)
    model_block = f"Model answer:\n{model_answer}\n\n" if model_answer else ""
    if criteria:
        crit_lines = "\n".join(
            f"- {c.get('label', 'point')} ({c.get('marks', 0)} marks): {c.get('description', '')}".rstrip()
            for c in criteria
        )
        criteria_block = (
            f"Marking rubric (award per point, partial credit allowed):\n{crit_lines}\n\n"
            f"Return a criterion_scores entry for each rubric point.\n\n"
        )
    else:
        criteria_block = ""
    return (
        f"You are a fair, supportive teacher grading a short written answer from a "
        f"student in {tier}\n\n"
        f"Question: {question_text}\n\n"
        f"{model_block}"
        f"{criteria_block}"
        f"Student's answer:\n{response_text}\n\n"
        f"Grade the answer out of {max_marks} marks. Reward correct ideas even if the "
        f"wording differs from the model answer; do not penalise spelling or phrasing. "
        f"Award partial credit where the student is partly right. Keep feedback "
        f"encouraging and specific about what to improve.\n\n"
        f"Call save_grade with your result."
    )


def _keyword_overlap_score(model_answer: str, response_text: str, max_marks: int) -> float:
    """Deterministic stub: fraction of model-answer keywords present in the response."""
    import re

    def _keywords(text: str) -> set[str]:
        return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 3}

    model_kw = _keywords(model_answer)
    if not model_kw:
        # No model answer to compare against — neutral half credit, low confidence.
        return round(max_marks * 0.5, 2)
    response_kw = _keywords(response_text)
    overlap = len(model_kw & response_kw) / len(model_kw)
    return round(max_marks * overlap, 2)


def _stub_open_grade(model_answer: str, response_text: str, max_marks: int) -> dict:
    score = _keyword_overlap_score(model_answer, response_text, max_marks)
    if score >= max_marks * 0.75:
        feedback = "Strong answer — it covers the key ideas. Review the model answer to polish the details."
    elif score >= max_marks * 0.4:
        feedback = "A reasonable attempt that captures some key points. Revisit the chapter to fill the gaps."
    else:
        feedback = "This answer misses several key ideas. Re-read the worked example and try explaining it again."
    return {
        "score": score,
        "feedback": feedback,
        "confidence": 0.3,  # heuristic — flag for teacher review
        "criterion_scores": [],
    }


def _shape_open_grade(data: dict, max_marks: int, model: str, in_tok: int, out_tok: int) -> dict:
    try:
        score = float(data.get("score", 0))
    except (TypeError, ValueError):
        score = 0.0
    score = max(0.0, min(score, float(max_marks)))
    try:
        confidence = float(data.get("confidence", 0.5))
    except (TypeError, ValueError):
        confidence = 0.5
    confidence = max(0.0, min(confidence, 1.0))
    raw_criteria = data.get("criterion_scores")
    criterion_scores = raw_criteria if isinstance(raw_criteria, list) else []
    return {
        "score": round(score, 2),
        "feedback": str(data.get("feedback", "")).strip(),
        "confidence": round(confidence, 2),
        "criterion_scores": criterion_scores,
        "model": model,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
    }


def grade_open_response(
    question_text: str,
    model_answer: str,
    criteria: list[dict],
    response_text: str,
    max_marks: int = 5,
    grade_level: int = 8,
) -> dict:
    """
    Suggest a grade for a student's free-text answer.

    Uses the standard provider cascade (Claude tool-use → Gemma/Ollama JSON →
    deterministic keyword-overlap stub) so it always returns a usable suggestion
    even with no LLM provider configured. The teacher reviews and can override.

    Returns:
        {"score": float, "feedback": str, "confidence": float,
         "criterion_scores": list, "model": str,
         "input_tokens": int, "output_tokens": int}
    """
    prompt = _build_open_grade_prompt(question_text, model_answer, criteria, response_text, max_marks, grade_level)

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if anthropic_key:
        try:
            result = _call_anthropic_tool(prompt, anthropic_key, _OPEN_GRADE_TOOL, OPEN_GRADE_MAX_TOKENS)
            if result:
                return _shape_open_grade(
                    result["data"], max_marks, result["model"], result["input_tokens"], result["output_tokens"]
                )
        except Exception:
            logger.exception("grade_open_response: Anthropic failed, trying next provider")

    json_hint = (
        "\n\nRespond ONLY with JSON: "
        '{"score": number, "feedback": "...", "confidence": number, '
        '"criterion_scores": [{"label": "...", "awarded": number, "max": number, "comment": "..."}]}'
    )

    google_key = os.environ.get("GOOGLE_AI_API_KEY", "")
    if google_key:
        try:
            import json as _json

            res = _call_google_ai_studio(prompt + json_hint, google_key)
            text = res["text"].lstrip("```json").lstrip("```").rstrip("```").strip()
            return _shape_open_grade(
                _json.loads(text), max_marks, res["model"], res["input_tokens"], res["output_tokens"]
            )
        except Exception:
            logger.exception("grade_open_response: Google AI Studio call failed, trying next provider")

    ollama_url = os.environ.get("OLLAMA_BASE_URL", OLLAMA_DEFAULT_URL)
    if _ollama_reachable(ollama_url):
        try:
            import json as _json

            res = _call_ollama(prompt + json_hint, ollama_url)
            text = res["text"].lstrip("```json").lstrip("```").rstrip("```").strip()
            return _shape_open_grade(
                _json.loads(text), max_marks, res["model"], res["input_tokens"], res["output_tokens"]
            )
        except Exception:
            logger.exception("grade_open_response: Ollama failed, falling back to stub")

    logger.warning("grade_open_response: no LLM provider available — returning stub")
    stub = _stub_open_grade(model_answer, response_text, max_marks)
    return {**stub, "model": "stub", "input_tokens": 0, "output_tokens": 0}


# ─────────────────────────────────────────────────────────────
# Teacher AI Assistant — Intervention Suggestions
# ─────────────────────────────────────────────────────────────

INTERVENTION_MAX_TOKENS = 450


def _build_intervention_prompt(stats: dict, subject_name: str, standard_number: int) -> str:
    name = stats.get("student_name", "this student")
    chapters = stats.get("focus_chapters", [])
    chapter_line = (
        "; ".join(f"{c['chapter_name']} ({c['avg_score']:.0%}, {c['severity']})" for c in chapters)
        if chapters
        else "none recorded"
    )
    labels = stats.get("misconception_labels", [])
    misconception_line = (
        "; ".join(f"{m['label']} (seen {m['count']}×)" for m in labels) if labels else "none diagnosed yet"
    )
    return (
        f"You are an experienced teaching coach helping a school teacher of "
        f"Standard {standard_number} {subject_name} support a struggling student.\n\n"
        f"Student: {name}\n"
        f"Average score across weak chapters: {stats.get('avg_score', 0.0):.0%}\n"
        f"Number of weak chapters: {stats.get('gap_count', 0)}\n"
        f"Weakest chapters: {chapter_line}\n"
        f"Recurring misconceptions: {misconception_line}\n\n"
        f"Write a short, concrete intervention plan (3–5 sentences) FOR THE TEACHER that:\n"
        f"- Names the specific chapter(s) to prioritise first and why.\n"
        f"- Suggests one or two concrete teaching actions (e.g. a targeted re-teach, "
        f"a worked example addressing the misconception, a small practice set).\n"
        f"- If a misconception is listed, says how to directly address that faulty idea.\n"
        f"- Ends with a simple way to check the student has recovered.\n"
        f"- Is practical and encouraging. Do NOT use markdown or bullet points.\n\n"
        f"Plan:"
    )


def _stub_intervention(stats: dict) -> str:
    name = stats.get("student_name", "This student")
    chapters = stats.get("focus_chapters", [])
    labels = stats.get("misconception_labels", [])

    if not chapters:
        return (
            f"{name} is showing early signs of falling behind. Sit with them for a few minutes "
            f"to find where the difficulty starts, then assign a short, easy practice set to rebuild confidence."
        )

    weakest = chapters[0]["chapter_name"]
    parts = [
        f"{name} is weakest in {weakest} (scoring {chapters[0]['avg_score']:.0%}), so start there.",
        f"Re-teach the core idea with one fresh worked example, then assign a short 4–5 question "
        f"practice set on {weakest} to check understanding.",
    ]
    if labels:
        parts.append(
            f"Watch for the recurring misconception '{labels[0]['label']}' and address it directly "
            f"before moving on."
        )
    if len(chapters) > 1:
        others = ", ".join(c["chapter_name"] for c in chapters[1:])
        parts.append(f"Once {weakest} improves, revisit {others}.")
    parts.append("Re-check with a quick exit question next week to confirm they have recovered.")
    return " ".join(parts)


def generate_intervention_plan(
    stats: dict,
    subject_name: str,
    standard_number: int,
) -> dict:
    """
    Generate a plain-language, teacher-facing intervention plan for one
    struggling student. Uses the same provider cascade as the other generators
    and always returns a usable plan — the stub composes a deterministic plan
    from the student's weak-chapter snapshot when no LLM provider is configured.

    Returns:
        {"text": str, "model": str, "input_tokens": int, "output_tokens": int}
    """
    prompt = _build_intervention_prompt(stats, subject_name, standard_number)

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if anthropic_key:
        try:
            logger.debug("generate_intervention_plan: using Anthropic Claude")
            return _call_anthropic_text(prompt, anthropic_key, INTERVENTION_MAX_TOKENS)
        except Exception:
            logger.exception("generate_intervention_plan: Anthropic failed, trying next provider")

    google_key = os.environ.get("GOOGLE_AI_API_KEY", "")
    if google_key:
        try:
            logger.debug("generate_intervention_plan: using Google AI Studio")
            return _call_google_ai_studio(prompt, google_key)
        except Exception:
            logger.exception("generate_intervention_plan: Google AI Studio call failed, trying next provider")

    ollama_url = os.environ.get("OLLAMA_BASE_URL", OLLAMA_DEFAULT_URL)
    if _ollama_reachable(ollama_url):
        try:
            logger.debug("generate_intervention_plan: using Ollama at %s", ollama_url)
            return _call_ollama(prompt, ollama_url)
        except Exception:
            logger.exception("generate_intervention_plan: Ollama failed, falling back to stub")

    logger.warning("generate_intervention_plan: no LLM provider available — returning stub")
    return {
        "text": _stub_intervention(stats),
        "model": "stub",
        "input_tokens": 0,
        "output_tokens": 0,
    }
