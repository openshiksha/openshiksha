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
