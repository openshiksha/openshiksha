"""
LLM client for AI-generated explanations.

Provider cascade (first available wins):
  1. Anthropic Claude   — set ANTHROPIC_API_KEY
  2. Google Gemma 4     — set GOOGLE_AI_API_KEY (Google AI Studio free tier)
  3. Ollama (Gemma)     — set OLLAMA_BASE_URL or run Ollama at localhost:11434
  4. Stub               — plain text fallback for dev/test with no keys

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
GEMMA_MODEL = "gemma-4-it"  # Gemma 4 instruction-tuned via Google AI Studio
OLLAMA_MODEL = "gemma3:4b"  # fallback if Gemma 4 not in local Ollama cache
OLLAMA_DEFAULT_URL = "http://localhost:11434"
MAX_TOKENS = 300


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


def _call_google_gemma(prompt: str, api_key: str) -> dict:
    """Call Gemma 4 via Google AI Studio (free tier)."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=GEMMA_MODEL,
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
        "model": GEMMA_MODEL,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }


def _call_ollama(prompt: str, base_url: str) -> dict:
    """Call a local Ollama instance (on-device, zero cost)."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
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
        "model": f"ollama/{OLLAMA_MODEL}",
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
      2. Google Gemma 4    — GOOGLE_AI_API_KEY env var (free tier)
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

    # 2. Google Gemma 4 (free tier via Google AI Studio)
    google_key = os.environ.get("GOOGLE_AI_API_KEY", "")
    if google_key:
        try:
            logger.debug("generate_explanation: using Google Gemma 4")
            return _call_google_gemma(prompt, google_key)
        except Exception:
            logger.exception("generate_explanation: Google Gemma call failed, trying next provider")

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
            return input_data.get("questions", [])
    return []


def _call_google_generate_questions(prompt: str, api_key: str) -> list[dict]:
    """Fallback: ask Gemma to return JSON and parse it."""
    import json as _json

    from google import genai
    from google.genai import types

    json_prompt = (
        prompt + "\n\nIMPORTANT: Respond ONLY with a valid JSON array of question objects, "
        'no markdown fences, no explanation. Example: [{"question_text": "...", ...}]'
    )
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=GEMMA_MODEL,
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
        "model": OLLAMA_MODEL,
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
            logger.debug("generate_questions: using Google Gemma 4")
            return _call_google_generate_questions(prompt, google_key)
        except Exception:
            logger.exception("generate_questions: Google Gemma failed, trying next provider")

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
            logger.debug("generate_class_summary: using Google Gemma 4")
            return _call_google_gemma(prompt, google_key)
        except Exception:
            logger.exception("generate_class_summary: Google Gemma failed, trying next provider")

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
