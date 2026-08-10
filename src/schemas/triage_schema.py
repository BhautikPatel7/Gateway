"""
src/schemas/triage_schema.py
─────────────────────────────
Pydantic models for the triage endpoint.

  TriageRequest  → what the user sends in the POST body
  TriageResult   → what the LLM must return (validated strictly)
"""

from typing import Literal
from pydantic import BaseModel, Field, field_validator


# ── Allowed values (single source of truth) ───────────────────────────────────

CATEGORIES = Literal[
    "billing",
    "refund",
    "shipping",
    "account",
    "security",
    "technical",
    "sales",
    "general",
    "out_of_scope",
]

PRIORITIES = Literal["P0", "P1", "P2", "P3"]

ACTIONS = Literal[
    "request_clarification",
    "route_to_billing",
    "route_to_refund",
    "route_to_shipping",
    "route_to_account",
    "route_to_security",
    "route_to_technical",
    "route_to_sales",
    "human_review",
    "no_action",
]


# ── Input ──────────────────────────────────────────────────────────────────────

class TriageRequest(BaseModel):
    """Body accepted by POST /api/triage."""

    message: str = Field(..., description="Raw customer message to classify.")

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message must not be empty or whitespace-only.")
        if len(stripped) > 4000:
            raise ValueError("Message is too long (max 4000 characters).")
        return stripped


# ── LLM Output ────────────────────────────────────────────────────────────────

class TriageResult(BaseModel):
    """
    Structured output produced by the LLM and validated by the policy engine.
    Every field is required — no extras allowed.
    """

    model_config = {"extra": "ignore"}   # silently drop any extra LLM fields

    category: CATEGORIES = Field(..., description="Primary support category.")
    priority: PRIORITIES = Field(..., description="Priority level P0–P3.")
    summary: str = Field(..., description="Short factual summary of the customer issue.")
    suggested_action: ACTIONS = Field(..., description="Recommended action to take.")
    needs_human: bool = Field(..., description="Whether a human agent must review this.")
    confidence: float = Field(..., description="Confidence score between 0.0 and 1.0.")

    @field_validator("summary")
    @classmethod
    def summary_not_empty(cls, v: str) -> str:
        if not v or len(v.strip()) < 5:
            raise ValueError("Summary must be at least 5 characters.")
        return v.strip()

    @field_validator("confidence")
    @classmethod
    def confidence_in_range(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0.")
        return round(v, 4)
