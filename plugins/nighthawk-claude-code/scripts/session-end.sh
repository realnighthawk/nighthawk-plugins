#!/bin/sh
# SessionEnd: spool a compact slice of the finished session so the next
# SessionStart can have the agent retain it through its own OAuth MCP
# connection. No network, no credential. Fail-open.
[ -n "${NIGHTHAWK_DISABLE_HOOKS:-}" ] && exit 0

event=$(cat)
field() { printf '%s' "$event" | sed -n "s/.*\"$1\":[[:space:]]*\"\([^\"]*\)\".*/\1/p"; }
transcript=$(field transcript_path)
session=$(field session_id)
[ -n "$transcript" ] && [ -f "$transcript" ] || exit 0

dir="${CLAUDE_PLUGIN_DATA:-$HOME/.cache/nighthawk}/retain-queue"
mkdir -p "$dir" 2>/dev/null || exit 0
out="$dir/$(printf '%s' "${session:-no-session}" | tr -c 'A-Za-z0-9_-' '_').txt"

TRANSCRIPT="$transcript" OUT="$out" python3 - <<'PY' 2>/dev/null || exit 0
import json, os

src, out = os.environ["TRANSCRIPT"], os.environ["OUT"]
cap = 120_000
skip_prefixes = ("<local-command", "<command-name>", "<command-message>",
                 "<command-args>", "<hippocampus-memory>")
lines, users = [], 0
with open(src, encoding="utf-8", errors="replace") as f:
    for raw in f:
        try:
            e = json.loads(raw)
        except Exception:
            continue
        if e.get("isMeta"):
            continue
        role = e.get("type")
        if role not in ("user", "assistant"):
            continue
        content = (e.get("message") or {}).get("content")
        if isinstance(content, str):
            parts = [content]
        elif isinstance(content, list):
            parts = [b.get("text", "") for b in content
                     if isinstance(b, dict) and b.get("type") == "text"]
        else:
            parts = []
        text = "\n".join(t for t in parts if t).strip()
        if not text or text.startswith(skip_prefixes):
            continue
        if role == "user":
            users += 1
        lines.append(f"{role}: {text}")

text = "\n\n".join(lines)
if users < 4 and len(text) < 4000:
    raise SystemExit(1)
with open(out, "w", encoding="utf-8") as f:
    f.write(text[-cap:])
PY

# Keep at most 10 spooled sessions.
ls -t "$dir" 2>/dev/null | tail -n +11 | while IFS= read -r f; do rm -f "$dir/$f"; done
exit 0
