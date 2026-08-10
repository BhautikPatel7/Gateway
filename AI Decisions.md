# AI Decisions

---

**Q1. What model and tools did you use?**

The main work is about defining category, priority matrix, and allowed actions — from this the LLM decides what output should be given.

- Model: `llama-3.1-8b-instant` via Groq (rate limits respected)
- Added role-based, few-shot prompting techniques for better results
- Tuned LLM parameters like temperature and max tokens for strict output
- Used Pydantic for validation schema so it guarantees correct structure from LLM
- Created an evaluation dataset and ran Pipeline evaluation — see `eval_report.md`
- Frontend built with HTML, CSS, and JavaScript

---

**Q2. What was your prompt strategy?**

The prompt was built with many things considered:

1. Role
2. Category definitions
3. Priority definitions
4. Escalation rules
5. Allowed actions
6. Few-shot examples
7. Output schema
8. Security instructions
9. Customer message

---

**Q3. How did you handle uncertainty and bad input?**

For uncertain questions, a separate `policy_engine` service was created that decides where a ticket goes — which rules need manual override, and which can be automated.

Garbage input is categorised as `out_of_scope` so it never goes to human review.

Policy rules applied after LLM:

1. **P0 Priority (Critical)** — Any P0 ticket always goes to human review. LLM decision is overridden.
2. **Security Escalation (P0 / P1)** — Routed directly to the security team, bypassing automation.
3. **Low Confidence** — If confidence score is below threshold, ticket goes to human review.
4. **Out-of-Scope (Garbage Input)** — Sets `needs_human = False` and `suggested_action = no_action`. Never escalated.

---

**Q4. How do you know it works?**

Created 20 sample inputs (13 train, 7 test) and ran the full pipeline to check accuracy and performance.

Used `ground_truth.json` for final evaluation of the pipeline.

See full results in `eval_report.md`.

---

**Q5. What would you fix with more time?**

1. Do more work on prompt engineering so the prompt is more effective and LLM gives more accurate answers
2. Add more validation and error handling
3. Add test cases for different scenarios
4. Connect with an actual backend so direct queries can be processed — moving from static JSON to real production use that helps organizations handle customer queries
5. Optimise with a smaller LLM model, add an `uncategorised` category — if the small LLM cannot classify it, pass to a higher intelligence system to save token cost
6. Work more closely on prompt to reduce input token count
7. Over time, add new categories, priorities, and actions based on data to increase accuracy
8. Create a maintainable repository and code for a long project.