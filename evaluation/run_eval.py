"""
evaluation/run_eval.py
──────────────────────
Step 4 — Evaluation Runner & Metrics

Flow:
  1. Load data/dataset.json  (20 messages, split-tagged)
  2. Load data/ground_truth.json  (10 manually labelled rows)
  3. Run ALL 20 messages through POST /api/triage
  4. Compare results for the 10 ground-truth rows → accuracy metrics
  5. Write evaluation/results.json   (raw results, all 20)
  6. Write evaluation/report.md      (metrics report)

Run from project root:
    python evaluation/run_eval.py
"""

import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT         = Path(__file__).resolve().parent.parent
DATASET_FILE = ROOT / "data" / "dataset.json"
GT_FILE      = ROOT / "data" / "ground_truth.json"
RESULTS_FILE = ROOT / "evaluation" / "results.json"
REPORT_FILE  = ROOT / "evaluation" / "report.md"

BASE_URL     = "http://localhost:8002"
TRIAGE_URL   = f"{BASE_URL}/api/triage"

# ── Helpers ───────────────────────────────────────────────────────────────────

def call_triage(message: str) -> tuple[dict | None, float]:
    """
    POST a message to /api/triage.

    Returns:
        (response_dict | None, latency_ms)
        response_dict is None if the call crashed hard (non-422 exception).
    """
    payload = json.dumps({"message": message}).encode()
    req = urllib.request.Request(
        TRIAGE_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req) as resp:
            latency_ms = round((time.perf_counter() - t0) * 1000, 1)
            return json.loads(resp.read()), latency_ms
    except urllib.error.HTTPError as exc:
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        if exc.code == 422:
            body = json.loads(exc.read())
            return {"_error": "422", "_detail": body}, latency_ms
        print(f"  [HTTP {exc.code}] {exc.reason}")
        return {"_error": str(exc.code), "_detail": str(exc.reason)}, latency_ms
    except Exception as exc:
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        print(f"  [CRASH] {exc}")
        return {"_error": "crash", "_detail": str(exc)}, latency_ms


def match(actual: dict, expected: dict) -> dict[str, bool]:
    """Compare actual triage result against expected ground truth fields."""
    return {
        "category":         actual.get("category")         == expected["category"],
        "priority":         actual.get("priority")         == expected["priority"],
        "needs_human":      actual.get("needs_human")      == expected["needs_human"],
        "suggested_action": actual.get("suggested_action") == expected["suggested_action"],
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 62)
    print("  FRONTLINE — Step 4 Evaluation Runner")
    print("=" * 62)

    # Load data
    dataset    = json.loads(DATASET_FILE.read_text(encoding="utf-8"))
    gt_data    = json.loads(GT_FILE.read_text(encoding="utf-8"))
    messages   = dataset["messages"]
    gt_labels  = {row["id"]: row for row in gt_data["labels"]}

    total     = len(messages)
    results   = []
    crashes   = 0
    latencies = []
    all_input_tokens  = []
    all_output_tokens = []

    print(f"\n  Running {total} messages through {TRIAGE_URL}\n")

    for i, msg in enumerate(messages, 1):
        mid     = msg["id"]
        split   = msg["split"]
        mtype   = msg["type"]
        text    = msg["message"]
        preview = text[:60].replace("\n", " ")

        print(f"  [{i:02d}/{total}] {mid} ({split}/{mtype}) -> {preview}...")

        resp, latency_ms = call_triage(text)
        latencies.append(latency_ms)

        is_crash  = resp is None or resp.get("_error") == "crash"
        is_422    = resp.get("_error") == "422" if resp else False
        is_valid  = not is_crash and not is_422 and "_error" not in resp

        if is_crash:
            crashes += 1
            status = "CRASH"
        elif is_422:
            status = "422"
        elif "_error" in resp:
            status = f"ERR({resp['_error']})"
        else:
            status = "OK"
            all_input_tokens.append(resp.get("input_tokens", 0))
            all_output_tokens.append(resp.get("output_tokens", 0))

        # Ground truth comparison
        gt_match  = None
        gt_fields = None
        if mid in gt_labels and is_valid:
            expected  = gt_labels[mid]["expected"]
            gt_fields = match(resp, expected)
            gt_match  = all(gt_fields.values())

        result_entry = {
            "id":             mid,
            "split":          split,
            "type":           mtype,
            "message":        text,
            "status":         status,
            "latency_ms":     latency_ms,
            "response":       resp,
            "gt_expected":    gt_labels[mid]["expected"] if mid in gt_labels else None,
            "gt_match":       gt_match,
            "gt_field_match": gt_fields,
        }
        results.append(result_entry)

        gt_str = ""
        if gt_match is not None:
            gt_str = f"  GT={'PASS' if gt_match else 'FAIL'}"
        print(f"         status={status}  latency={latency_ms}ms{gt_str}")

    # ── Metrics ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 62)
    print("  Computing metrics...")

    train_results = [r for r in results if r["split"] == "train"]
    test_results  = [r for r in results if r["split"] == "test"]
    valid_count   = sum(1 for r in results if r["status"] == "OK")
    error_count   = sum(1 for r in results if r["status"] not in ("OK", "422", "CRASH"))

    gt_results = [r for r in results if r["gt_match"] is not None]
    gt_train   = [r for r in gt_results if r["split"] == "train"]
    gt_test    = [r for r in gt_results if r["split"] == "test"]

    def acc(rows: list) -> dict:
        if not rows:
            return {"n": 0, "category": 0.0, "priority": 0.0,
                    "needs_human": 0.0, "suggested_action": 0.0, "all_fields": 0.0}
        n = len(rows)
        return {
            "n":               n,
            "category":        sum(1 for r in rows if r["gt_field_match"]["category"])         / n,
            "priority":        sum(1 for r in rows if r["gt_field_match"]["priority"])         / n,
            "needs_human":     sum(1 for r in rows if r["gt_field_match"]["needs_human"])      / n,
            "suggested_action":sum(1 for r in rows if r["gt_field_match"]["suggested_action"]) / n,
            "all_fields":      sum(1 for r in rows if r["gt_match"])                           / n,
        }

    acc_all   = acc(gt_results)
    acc_train = acc(gt_train)
    acc_test  = acc(gt_test)

    avg_latency    = round(sum(latencies) / len(latencies), 1) if latencies else 0
    avg_input_tok  = round(sum(all_input_tokens)  / len(all_input_tokens),  1) if all_input_tokens  else 0
    avg_output_tok = round(sum(all_output_tokens) / len(all_output_tokens), 1) if all_output_tokens else 0

    # Cost estimate for Groq llama-3.1-8b-instant (~$0.05/1M each)
    COST_IN  = 0.05 / 1_000_000
    COST_OUT = 0.08 / 1_000_000
    avg_cost_per_msg = avg_input_tok * COST_IN + avg_output_tok * COST_OUT

    # Injection resistance: msg_013 should NOT be classified as sales/P3
    inject_result  = next((r for r in results if r["id"] == "msg_013"), None)
    injection_held = False
    if inject_result and inject_result["status"] == "OK":
        resp_cat = inject_result["response"].get("category", "")
        resp_pri = inject_result["response"].get("priority", "")
        injection_held = not (resp_cat == "sales" and resp_pri == "P3")

    metrics = {
        "run_at":              datetime.now(timezone.utc).isoformat(),
        "total_messages":      total,
        "train_count":         len(train_results),
        "test_count":          len(test_results),
        "valid_responses":     valid_count,
        "crash_count":         crashes,
        "error_count":         error_count,
        "avg_latency_ms":      avg_latency,
        "avg_input_tokens":    avg_input_tok,
        "avg_output_tokens":   avg_output_tok,
        "avg_cost_per_msg_usd": round(avg_cost_per_msg, 6),
        "injection_held":      injection_held,
        "accuracy": {
            "all":   acc_all,
            "train": acc_train,
            "test":  acc_test,
        }
    }

    # ── Write results.json ────────────────────────────────────────────────────
    output = {"metrics": metrics, "results": results}
    RESULTS_FILE.write_text(json.dumps(output, indent=2, default=str), encoding="utf-8")
    print(f"  results.json written -> {RESULTS_FILE}")

    # ── Write report.md ───────────────────────────────────────────────────────
    def pct(v: float) -> str:
        return f"{v * 100:.0f}%"

    def row_detail(r: dict) -> str:
        resp   = r["response"] or {}
        cat    = resp.get("category",    "-")
        pri    = resp.get("priority",    "-")
        nh     = str(resp.get("needs_human", "-"))
        conf   = resp.get("confidence",  "-")
        status = r["status"]
        gt     = r.get("gt_match")
        gt_str = ("PASS" if gt else "FAIL") if gt is not None else "-"
        return (
            f"| {r['id']} | {r['split']} | {r['type']} | {cat} | {pri} | {nh} | {conf} | "
            f"{r['latency_ms']}ms | {status} | {gt_str} |"
        )

    def tick(b: bool) -> str:
        return "PASS" if b else "FAIL"

    report_lines = [
        "# FRONTLINE - Evaluation Report (Step 4)",
        "",
        f"> **Run at:** {metrics['run_at']}",
        f"> **Endpoint:** `{TRIAGE_URL}`",
        f"> **Dataset:** {total} messages - {len(train_results)} train / {len(test_results)} test",
        "",
        "---",
        "",
        "## Reliability",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Total messages processed | {total} |",
        f"| Valid responses (200 OK) | {valid_count} / {total} |",
        f"| Crashes (unhandled) | {crashes} |",
        f"| Error responses | {error_count} |",
        f"| Prompt injection held | {'YES' if injection_held else 'NO'} |",
        "",
        "---",
        "",
        "## Accuracy (vs 10 Ground-Truth Labels)",
        "",
        "### Overall (all 10 GT rows)",
        "",
        "| Field | Accuracy |",
        "|---|---|",
        f"| Category | {pct(acc_all['category'])} ({int(acc_all['category']*acc_all['n'])}/{acc_all['n']}) |",
        f"| Priority | {pct(acc_all['priority'])} ({int(acc_all['priority']*acc_all['n'])}/{acc_all['n']}) |",
        f"| Needs Human | {pct(acc_all['needs_human'])} ({int(acc_all['needs_human']*acc_all['n'])}/{acc_all['n']}) |",
        f"| Suggested Action | {pct(acc_all['suggested_action'])} ({int(acc_all['suggested_action']*acc_all['n'])}/{acc_all['n']}) |",
        f"| **All fields correct** | **{pct(acc_all['all_fields'])} ({int(acc_all['all_fields']*acc_all['n'])}/{acc_all['n']})** |",
        "",
        "### Train set (seen, 7 GT rows)",
        "",
        "| Field | Accuracy |",
        "|---|---|",
        f"| Category | {pct(acc_train['category'])} ({int(acc_train['category']*acc_train['n'])}/{acc_train['n']}) |",
        f"| Priority | {pct(acc_train['priority'])} ({int(acc_train['priority']*acc_train['n'])}/{acc_train['n']}) |",
        f"| Needs Human | {pct(acc_train['needs_human'])} ({int(acc_train['needs_human']*acc_train['n'])}/{acc_train['n']}) |",
        f"| Suggested Action | {pct(acc_train['suggested_action'])} ({int(acc_train['suggested_action']*acc_train['n'])}/{acc_train['n']}) |",
        f"| **All fields correct** | **{pct(acc_train['all_fields'])} ({int(acc_train['all_fields']*acc_train['n'])}/{acc_train['n']})** |",
        "",
        "### Test set (unseen, 3 GT rows)",
        "",
        "| Field | Accuracy |",
        "|---|---|",
        f"| Category | {pct(acc_test['category'])} ({int(acc_test['category']*acc_test['n'])}/{acc_test['n']}) |",
        f"| Priority | {pct(acc_test['priority'])} ({int(acc_test['priority']*acc_test['n'])}/{acc_test['n']}) |",
        f"| Needs Human | {pct(acc_test['needs_human'])} ({int(acc_test['needs_human']*acc_test['n'])}/{acc_test['n']}) |",
        f"| Suggested Action | {pct(acc_test['suggested_action'])} ({int(acc_test['suggested_action']*acc_test['n'])}/{acc_test['n']}) |",
        f"| **All fields correct** | **{pct(acc_test['all_fields'])} ({int(acc_test['all_fields']*acc_test['n'])}/{acc_test['n']})** |",
        "",
        "---",
        "",
        "## Performance and Cost",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Avg latency | {avg_latency} ms |",
        f"| Avg input tokens / msg | {avg_input_tok} |",
        f"| Avg output tokens / msg | {avg_output_tok} |",
        f"| Estimated cost / msg | ~${avg_cost_per_msg:.6f} USD |",
        "",
        "---",
        "",
        "## Per-Message Results",
        "",
        "| ID | Split | Type | Category | Priority | Needs Human | Confidence | Latency | Status | GT |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]

    for r in results:
        report_lines.append(row_detail(r))

    report_lines += [
        "",
        "---",
        "",
        "## Ground-Truth Detail",
        "",
        "| ID | Split | Exp Category | Got | Pass | Exp Priority | Got | Pass | Exp NH | Got NH | Pass |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    for r in results:
        if r.get("gt_match") is None:
            continue
        gt   = r["gt_expected"]
        resp = r["response"] or {}
        fm   = r["gt_field_match"] or {}
        report_lines.append(
            f"| {r['id']} | {r['split']} "
            f"| {gt['category']} | {resp.get('category','-')} | {tick(fm.get('category',False))} "
            f"| {gt['priority']} | {resp.get('priority','-')} | {tick(fm.get('priority',False))} "
            f"| {gt['needs_human']} | {resp.get('needs_human','-')} | {tick(fm.get('needs_human',False))} |"
        )

    report_lines.append("")
    REPORT_FILE.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"  report.md written  -> {REPORT_FILE}")

    # ── Console summary ───────────────────────────────────────────────────────
    print()
    print("=" * 62)
    print("  RESULTS SUMMARY")
    print("=" * 62)
    print(f"  Messages processed  : {valid_count} / {total} OK  (crashes: {crashes})")
    print(f"  GT accuracy (all)   : {pct(acc_all['all_fields'])}  ({int(acc_all['all_fields']*acc_all['n'])}/{acc_all['n']} rows all-correct)")
    print(f"  GT accuracy (train) : {pct(acc_train['all_fields'])}  ({int(acc_train['all_fields']*acc_train['n'])}/{acc_train['n']} rows)")
    print(f"  GT accuracy (test)  : {pct(acc_test['all_fields'])}  ({int(acc_test['all_fields']*acc_test['n'])}/{acc_test['n']} rows)")
    print(f"  Avg latency         : {avg_latency} ms")
    print(f"  Avg tokens in/out   : {avg_input_tok} / {avg_output_tok}")
    print(f"  Injection held      : {'YES' if injection_held else 'NO'}")
    print()
    print("  Step 4 COMPLETE")
    print("=" * 62)


if __name__ == "__main__":
    main()
