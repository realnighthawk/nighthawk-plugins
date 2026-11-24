#!/bin/sh
# SessionEnd: retain a compact slice of the finished session in the workspace's memory (Hindsight REST, through the router).
# Runs only under `mc claude` (MC_MEMORY_TOKEN set); anywhere else it does nothing. Tool output is never sent. Fail-open.
[ -n "${MISSION_CONTROL_DISABLE_HOOKS:-}" ] && exit 0
[ -n "${MC_MEMORY_TOKEN:-}" ] || exit 0

EVENT=$(cat) python3 - <<'PY' 2>/dev/null || exit 0
import json, os, urllib.request

event = json.loads(os.environ["EVENT"])
src = event.get("transcript_path", "")
if not os.path.isfile(src):
    raise SystemExit(0)
skip = ("<local-command", "<command-name>", "<command-message>", "<command-args>", "<memory>")
lines, users = [], 0
for raw in open(src, encoding="utf-8", errors="replace"):
    try:
        e = json.loads(raw)
    except Exception:
        continue
    role = e.get("type")
    if e.get("isMeta") or role not in ("user", "assistant"):
        continue
    c = (e.get("message") or {}).get("content")
    parts = [c] if isinstance(c, str) else [b.get("text", "") for b in c or [] if isinstance(b, dict) and b.get("type") == "text"]
    text = "\n".join(t for t in parts if t).strip()
    if text and not text.startswith(skip):
        users += role == "user"
        lines.append(f"{role}: {text}")
text = "\n\n".join(lines)
if users < 4 and len(text) < 4000:
    raise SystemExit(0)

base, bank = os.environ["MC_MEMORY_URL"], os.environ.get("MC_MEMORY_BANK", "claude-code")
body = {"items": [{"content": text[-120_000:], "context": f"Claude Code session in {os.path.basename(event.get('cwd') or os.getcwd())}"}], "async": True}
req = urllib.request.Request(
    f"{base}/v1/default/banks/{bank}/memories", data=json.dumps(body).encode(),
    headers={"Authorization": "Bearer " + os.environ["MC_MEMORY_TOKEN"], "Content-Type": "application/json", "User-Agent": "mission-control-hook/1"},
)
urllib.request.urlopen(req, timeout=25).read()
PY
exit 0
