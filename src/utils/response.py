"""
src/utils/response.py
─────────────────────
Common API response builder.

Every route must use `build_response()` to wrap its payload.
This ensures every response includes:
  - request_id      : unique UUID for this request
  - processing_time_ms : wall-clock time from call to return
  - input_tokens    : LLM input tokens used (0 if no LLM call)
  - output_tokens   : LLM output tokens used (0 if no LLM call)
  - total_tokens    : input_tokens + output_tokens

Usage:
    from src.utils.response import ResponseBuilder

    builder = ResponseBuilder()          # start timer
    result  = do_work()
    return builder.build(data=result, input_tokens=50, output_tokens=30)
"""

import uuid
import time
from typing import Any


class ResponseBuilder:
    """
    Start this at the beginning of a request handler.
    Call .build() when ready to return the response.
    """

    def __init__(self) -> None:
        self.request_id: str = str(uuid.uuid4())
        self._start: float = time.perf_counter()

    def build(
        self,
        data: dict[str, Any],
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> dict[str, Any]:
        """
        Merge the payload with standard metadata fields.

        Args:
            data:          The main response payload (dict).
            input_tokens:  Tokens sent to the LLM.
            output_tokens: Tokens received from the LLM.

        Returns:
            dict with data fields + metadata fields at the top level.
        """
        elapsed_ms = round((time.perf_counter() - self._start) * 1000, 2)

        metadata = {
            "request_id": self.request_id,
            "processing_time_ms": elapsed_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
        }

        # Metadata sits alongside the data fields (flat structure)
        return {**data, **metadata}
