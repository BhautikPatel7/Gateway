# FRONTLINE - Evaluation Report (Step 4)

> **Run at:** 2026-08-10T15:36:44.145566+00:00
> **Endpoint:** `http://localhost:8002/api/triage`
> **Dataset:** 20 messages - 14 train / 6 test

---

## Reliability

| Metric | Value |
|---|---|
| Total messages processed | 20 |
| Valid responses (200 OK) | 20 / 20 |
| Crashes (unhandled) | 0 |
| Error responses | 0 |
| Prompt injection held | YES |

---

## Accuracy (vs 10 Ground-Truth Labels)

### Overall (all 10 GT rows)

| Field | Accuracy |
|---|---|
| Category | 100% (10/10) |
| Priority | 100% (10/10) |
| Needs Human | 100% (10/10) |
| Suggested Action | 90% (9/10) |
| **All fields correct** | **90% (9/10)** |

### Train set (seen, 7 GT rows)

| Field | Accuracy |
|---|---|
| Category | 100% (7/7) |
| Priority | 100% (7/7) |
| Needs Human | 100% (7/7) |
| Suggested Action | 86% (6/7) |
| **All fields correct** | **86% (6/7)** |

### Test set (unseen, 3 GT rows)

| Field | Accuracy |
|---|---|
| Category | 100% (3/3) |
| Priority | 100% (3/3) |
| Needs Human | 100% (3/3) |
| Suggested Action | 100% (3/3) |
| **All fields correct** | **100% (3/3)** |

---

## Performance and Cost

| Metric | Value |
|---|---|
| Avg latency | 16528.3 ms |
| Avg input tokens / msg | 1885.2 |
| Avg output tokens / msg | 60.4 |
| Estimated cost / msg | ~$0.000099 USD |

---

## Per-Message Results

| ID | Split | Type | Category | Priority | Needs Human | Confidence | Latency | Status | GT |
|---|---|---|---|---|---|---|---|---|---|
| msg_001 | train | billing | billing | P1 | True | 0.95 | 2886.1ms | OK | PASS |
| msg_002 | train | billing | billing | P1 | True | 0.95 | 2526.1ms | OK | - |
| msg_003 | train | refund | refund | P2 | False | 0.95 | 2971.9ms | OK | PASS |
| msg_004 | train | refund | refund | P3 | False | 0.95 | 13134.2ms | OK | - |
| msg_005 | train | shipping | shipping | P2 | False | 0.95 | 18826.5ms | OK | - |
| msg_006 | train | shipping | shipping | P2 | False | 0.92 | 19662.0ms | OK | PASS |
| msg_007 | train | account | account | P2 | False | 0.91 | 21775.5ms | OK | - |
| msg_008 | train | security | security | P0 | True | 0.98 | 18068.5ms | OK | PASS |
| msg_009 | train | technical | technical | P2 | False | 0.9 | 18731.4ms | OK | - |
| msg_010 | train | general | general | P3 | False | 0.95 | 19806.7ms | OK | - |
| msg_011 | train | multi_intent | billing | P1 | True | 0.82 | 16818.9ms | OK | PASS |
| msg_012 | train | ambiguous | account | P2 | True | 0.45 | 16953.9ms | OK | FAIL |
| msg_013 | train | adversarial | out_of_scope | P3 | False | 0.99 | 21735.2ms | OK | PASS |
| msg_014 | train | clear | shipping | P3 | False | 0.95 | 19911.8ms | OK | - |
| msg_015 | test | billing | billing | P1 | True | 0.95 | 19583.3ms | OK | PASS |
| msg_016 | test | security | account | P3 | False | 0.94 | 19599.2ms | OK | PASS |
| msg_017 | test | shipping | shipping | P2 | False | 0.92 | 19553.4ms | OK | - |
| msg_018 | test | multi_intent | technical | P2 | False | 0.95 | 19894.7ms | OK | - |
| msg_019 | test | garbage | out_of_scope | P3 | False | 1.0 | 18593.3ms | OK | - |
| msg_020 | test | refund | refund | P2 | False | 0.91 | 19534.4ms | OK | PASS |

---

## Ground-Truth Detail

| ID | Split | Exp Category | Got | Pass | Exp Priority | Got | Pass | Exp NH | Got NH | Pass |
|---|---|---|---|---|---|---|---|---|---|---|
| msg_001 | train | billing | billing | PASS | P1 | P1 | PASS | True | True | PASS |
| msg_003 | train | refund | refund | PASS | P2 | P2 | PASS | False | False | PASS |
| msg_006 | train | shipping | shipping | PASS | P2 | P2 | PASS | False | False | PASS |
| msg_008 | train | security | security | PASS | P0 | P0 | PASS | True | True | PASS |
| msg_011 | train | billing | billing | PASS | P1 | P1 | PASS | True | True | PASS |
| msg_012 | train | account | account | PASS | P2 | P2 | PASS | True | True | PASS |
| msg_013 | train | out_of_scope | out_of_scope | PASS | P3 | P3 | PASS | False | False | PASS |
| msg_015 | test | billing | billing | PASS | P1 | P1 | PASS | True | True | PASS |
| msg_016 | test | account | account | PASS | P3 | P3 | PASS | False | False | PASS |
| msg_020 | test | refund | refund | PASS | P2 | P2 | PASS | False | False | PASS |
