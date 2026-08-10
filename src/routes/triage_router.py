"""
src/routes/triage_router.py
────────────────────────────
POST /api/triage — customer message triage endpoint.

Pipeline:
  1. Input validation  (Pydantic TriageRequest)
  2. LLM classification  (llm_service.classify)
  3. Policy enforcement  (policy_engine.apply)
  4. Response wrapping   (ResponseBuilder — adds request_id, tokens, timing)
"""

from fastapi import APIRouter, HTTPException
from src.logger import get_logger
from src.schemas.triage_schema import TriageRequest, TriageResult
from src.services import llm_service, policy_engine
from src.utils.response import ResponseBuilder

logger = get_logger(__name__)

router = APIRouter(prefix="/api/triage", tags=["Triage"])


@router.post("", summary="Triage a customer message")
async def triage(request: TriageRequest) -> dict:
    """
    Classify a raw customer support message into a structured triage decision.

    **Request body**
    ```json
    { "message": "I was charged twice for my order!" }
    ```

    **Response** includes the triage result plus request metadata:
    - `request_id` — unique UUID for this call
    - `processing_time_ms` — end-to-end wall-clock time
    - `input_tokens` / `output_tokens` / `total_tokens` — Groq token usage
    """
    builder = ResponseBuilder()

    try:
        # Step 1: LLM classification
        llm_result, input_tokens, output_tokens = llm_service.classify(request.message)

        # Step 2: Policy enforcement
        final_result: TriageResult = policy_engine.apply(llm_result)

    except Exception as exc:
        logger.error("Triage pipeline error: %s", exc)
        raise HTTPException(status_code=500, detail="Triage processing failed. Please try again.")

    return builder.build(
        data=final_result.model_dump(),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
