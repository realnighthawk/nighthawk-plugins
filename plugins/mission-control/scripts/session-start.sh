#!/bin/sh
# SessionStart: recall from the workspace's memory (Hindsight REST, through the router) and hand the result to the agent as context.
# Runs only under `mc claude`, which sets MC_MEMORY_TOKEN; anywhere else it does nothing. Fail-open: a slow or failed recall never blocks the session.
[ -n "${MISSION_CONTROL_DISABLE_HOOKS:-}" ] && exit 0
[ -n "${MC_MEMORY_TOKEN:-}" ] || exit 0
cat >/dev/null 2>&1 || true

python3 - <<'PY' 2>/dev/null || exit 0
import json, os, urllib.request

base, bank = os.environ["MC_MEMORY_URL"], os.environ.get("MC_MEMORY_BANK", "claude-code")
project = os.path.basename(os.getcwd())
req = urllib.request.Request(
    f"{base}/v1/default/banks/{bank}/memories/recall",
    data=json.dumps({"query": f"the user, their preferences and decisions, and the project {project}", "max_tokens": 1500}).encode(),
    headers={"Authorization": "Bearer " + os.environ["MC_MEMORY_TOKEN"], "Content-Type": "application/json", "User-Agent": "mission-control-hook/1"},
)
with urllib.request.urlopen(req, timeout=15) as r:
    facts = [x["text"] for x in json.load(r).get("results", []) if x.get("text")]
if facts:
    ctx = "<memory>\nWhat is remembered about the user and this project (recalled at session start):\n" + "\n".join("- " + f for f in facts) + "\n</memory>"
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}))
PY
exit 0
