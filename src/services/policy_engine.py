"""
src/services/policy_engine.py
──────────────────────────────
Deterministic business rules applied AFTER the LLM produces a TriageResult.

The LLM handles intent understanding and classification.
This module enforces company policy — rules that must ALWAYS hold,
regardless of what the LLM returned.

apply(result, confidence_threshold)  →  TriageResult (possibly modified)
"""

from src.config import settings
from src.logger import get_logger
from src.schemas.triage_schema import TriageResult

logger = get_logger(__name__)


def apply(result: TriageResult) -> TriageResult:
    """
    Apply all business rules to a TriageResult returned by the LLM.

    Rules are applied in priority order. Each rule may override
    needs_human and suggested_action.

    Args:
        result: The TriageResult produced by the LLM.

    Returns:
        TriageResult: The (possibly modified) result after policy enforcement.
    """
    # Work with a mutable copy
    data = result.model_dump()
    threshold = settings.CONFIDENCE_THRESHOLD

    # ── Rule 1: P0 always escalates to human ─────────────────────────────────
    if data["priority"] == "P0":
        if not data["needs_human"]:
            logger.info("Policy: P0 priority -> forcing needs_human=True")
        data["needs_human"] = True
        if data["suggested_action"] not in ("route_to_security", "human_review"):
            data["suggested_action"] = "human_review"

    # ── Rule 2: Active security (P0/P1) always escalates ─────────────────────
    if data["category"] == "security" and data["priority"] in ("P0", "P1"):
        if not data["needs_human"]:
            logger.info("Policy: security P0/P1 -> forcing needs_human=True")
        data["needs_human"] = True
        data["suggested_action"] = "route_to_security"

    # ── Rule 3: Low confidence → human review ────────────────────────────────
    if data["confidence"] < threshold:
        if not data["needs_human"]:
            logger.info(
                "Policy: confidence %.2f < %.2f -> forcing needs_human=True",
                data["confidence"], threshold,
            )
        data["needs_human"] = True
        data["suggested_action"] = "human_review"

    # ── Rule 4: Out-of-scope → no action, no human needed ────────────────────
    if data["category"] == "out_of_scope":
        data["needs_human"] = False
        data["suggested_action"] = "no_action"
        logger.info("Policy: out_of_scope -> no_action, needs_human=False")

    return TriageResult(**data)
