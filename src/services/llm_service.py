"""
src/services/llm_service.py
────────────────────────────
Groq LLM call for message triage.

classify(message)  →  (TriageResult, input_tokens, output_tokens)

Retries up to MAX_RETRIES times if the LLM returns invalid JSON or
fails Pydantic validation. Returns a safe fallback after all retries fail.
"""

import json
import time

from groq import Groq
from pydantic import ValidationError

from src.config import settings
from src.logger import get_logger
from src.prompts.triage_prompt import build_system_prompt, build_user_message
from src.schemas.triage_schema import TriageResult

logger = get_logger(__name__)

MAX_RETRIES = 2

# Groq client — created once at import time
_client = Groq(api_key=settings.GROQ_API_KEY)

# System prompt — built once at import time
_SYSTEM_PROMPT = build_system_prompt()


def classify(message: str) -> tuple[TriageResult, int, int]:
    """
    Send a customer message to the Groq LLM and return a validated TriageResult.

    Args:
        message: Raw customer message (already validated by TriageRequest).

    Returns:
        Tuple of (TriageResult, input_tokens, output_tokens).
        On complete failure, returns a safe fallback result with 0 tokens.
    """
    user_msg = build_user_message(message)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.debug("LLM call attempt %d for message: %.60s...", attempt, message)

            response = _client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user",   "content": user_msg},
                ],
                temperature=0.1,       # low temperature for consistent structured output
                max_tokens=300,        # triage response is short
                response_format={"type": "json_object"},  # force JSON mode
            )

            raw_content = response.choices[0].message.content or ""
            input_tokens  = response.usage.prompt_tokens     if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0

            logger.debug("LLM raw response: %s", raw_content[:200])

            # Parse JSON
            data = json.loads(raw_content)

            # Validate with Pydantic
            result = TriageResult(**data)

            logger.info(
                "Triage OK | category=%s priority=%s confidence=%.2f needs_human=%s",
                result.category, result.priority, result.confidence, result.needs_human,
            )
            return result, input_tokens, output_tokens

        except json.JSONDecodeError as exc:
            logger.warning("Attempt %d: LLM returned invalid JSON — %s", attempt, exc)

        except ValidationError as exc:
            logger.warning("Attempt %d: Pydantic validation failed — %s", attempt, exc)

        except Exception as exc:
            logger.error("Attempt %d: Unexpected LLM error — %s", attempt, exc)

        # Small pause before retry to avoid hammering the API
        if attempt < MAX_RETRIES:
            time.sleep(1)

    # All retries exhausted — return a safe fallback
    logger.error("All %d LLM attempts failed. Returning safe fallback.", MAX_RETRIES)
    fallback = TriageResult(
        category="general",
        priority="P2",
        summary="Unable to classify this message automatically. Requires human review.",
        suggested_action="human_review",
        needs_human=True,
        confidence=0.0,
    )
    return fallback, 0, 0
