# Gateway — AI Customer Message Triage System

An LLM-powered backend that classifies incoming customer messages into categories, priorities, and recommended actions — with a deterministic policy engine layered on top.

---

## Architecture Overview

```
Customer Message (HTTP POST)
        │
        ▼
┌─────────────────┐
│   FastAPI App   │  ← src/app.py
│  (src/routes/)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   LLM Service   │  ← src/services/llm_service.py
│  Groq API       │
│  llama-3.1-8b   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Triage Prompt  │  ← src/prompts/triage_prompt.py
│  (structured)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Pydantic Schema │  ← src/schemas/triage_schema.py
│  (validation)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Policy Engine   │  ← src/services/policy_engine.py
│ (business rules)│
└────────┬────────┘
         │
         ▼
    TriageResult (JSON response)
```

---

## Components

### 1. Entry Point — `main.py`
Starts the Uvicorn server with settings from `.env`.

### 2. FastAPI App — `src/app.py`
- Registers all routers
- Serves the frontend (`static/index.html`) at `/`
- Mounts static assets at `/static`
- Exposes API docs at `/docs`

### 3. Routes — `src/routes/`
| File | Endpoint | Purpose |
|---|---|---|
| `triage_router.py` | `POST /api/triage` | Accepts customer message, returns triage result |
| `health_router.py` | `GET /api/health` | Health check |

### 4. LLM Service — `src/services/llm_service.py`
- Calls Groq API with model `llama-3.1-8b-instant`
- Sends a structured prompt built by `triage_prompt.py`
- Returns raw LLM output for schema validation

### 5. Prompt — `src/prompts/triage_prompt.py`
Prompt is built with all context the LLM needs:
- Role definition
- Category definitions
- Priority matrix
- Escalation rules
- Allowed actions
- Few-shot examples
- Output schema
- Security instructions
- Customer message

### 6. Pydantic Schema — `src/schemas/triage_schema.py`
Validates every LLM response. Fields:
| Field | Type | Description |
|---|---|---|
| `category` | string | billing, refund, shipping, account, security, technical, sales, general, out_of_scope |
| `priority` | string | P0 (critical) → P3 (low) |
| `summary` | string | Short factual summary of the issue |
| `suggested_action` | string | What action to take |
| `needs_human` | bool | Whether a human must review |
| `confidence` | float | LLM confidence score 0.0 – 1.0 |

### 7. Policy Engine — `src/services/policy_engine.py`
Deterministic rules applied **after** the LLM. Overrides LLM decisions when needed:

| Rule | Condition | Outcome |
|---|---|---|
| 1 | Priority is P0 | Force `needs_human = True` |
| 2 | Category is security + P0/P1 | Route to security team |
| 3 | Confidence below threshold | Force `needs_human = True` |
| 4 | Category is `out_of_scope` | Set `no_action`, skip human review |

### 8. Config — `src/config.py`
Reads all settings from `.env` using Pydantic Settings. Fails fast on startup if required values are missing.

### 9. Frontend — `static/index.html`
Simple HTML/CSS/JS UI served directly by FastAPI. Sends customer messages to the triage API and displays structured results.

---

## Data Flow (Step by Step)

1. User submits a customer message via the UI or API
2. `triage_router` receives the `POST /api/triage` request
3. `llm_service` builds a structured prompt and calls Groq API
4. LLM returns a JSON response
5. Pydantic validates the structure — rejects any malformed output
6. `policy_engine` applies business rules — may override LLM decisions
7. Final `TriageResult` is returned as JSON

---

## Key Design Decisions

- **LLM for intent, policy engine for rules** — the LLM understands language; the policy engine enforces non-negotiable business rules
- **Garbage input → out_of_scope** — bad/irrelevant input is never sent to a human queue
- **Pydantic validation** — guarantees the LLM can never return a malformed structure
- **Fail-fast config** — app won't start if `.env` is misconfigured

---

## Related Files

- `STARTUP.md` — how to set up and run the app
- `AI Decisions.md` — design and model decisions Q&A
- `eval_report.md` — pipeline evaluation results
