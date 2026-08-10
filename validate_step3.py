"""Live endpoint tests for Step 3."""
import urllib.request, json, urllib.error

BASE = "http://localhost:8002"

def post(msg):
    req = urllib.request.Request(
        f"{BASE}/api/triage",
        data=json.dumps({"message": msg}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return urllib.request.urlopen(req)

# ── Test 1: Empty message → 422 ───────────────────────────────────────────────
try:
    post("   ")
    print("Test 1 FAIL: expected 422 for empty message")
except urllib.error.HTTPError as e:
    status = "PASS" if e.code == 422 else f"FAIL (got {e.code})"
    print(f"Test 1 - Empty message rejected : {status}")

# ── Test 2: Active security compromise ───────────────────────────────────────
resp = json.loads(post("Someone hacked my account and changed my password right now!").read())
nh = resp["needs_human"]
cat = resp["category"]
pri = resp["priority"]
ok = nh and pri in ("P0", "P1") and cat == "security"
print(f"Test 2 - Active security         : category={cat} priority={pri} needs_human={nh} -> {'PASS' if ok else 'FAIL'}")

# ── Test 3: Response shape has all required fields ────────────────────────────
required = [
    "category", "priority", "summary", "suggested_action",
    "needs_human", "confidence",
    "request_id", "processing_time_ms",
    "input_tokens", "output_tokens", "total_tokens",
]
missing = [k for k in required if k not in resp]
print(f"Test 3 - Response shape          : {'PASS' if not missing else 'FAIL missing=' + str(missing)}")
print(f"         request_id={resp['request_id'][:8]}... time={resp['processing_time_ms']}ms tokens={resp['total_tokens']}")

# ── Test 4: Health check still works ─────────────────────────────────────────
hreq = urllib.request.urlopen(f"{BASE}/api/health")
hresp = json.loads(hreq.read())
print(f"Test 4 - Health check            : status={hresp.get('status')} -> {'PASS' if hresp.get('status')=='ok' else 'FAIL'}")

print()
print("Step 3 COMPLETE")
