#!/bin/sh
# One runnable check for the memory hook scripts: fabricate a session, spool
# it at SessionEnd, and assert the next SessionStart names it.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

f="$tmp/transcript.jsonl"
{
  echo '{"type":"user","message":{"content":"decide: use Reactor for the hub"}}'
  echo '{"type":"assistant","message":{"content":[{"type":"text","text":"Agreed."}]}}'
  echo '{"type":"user","message":{"content":[{"type":"tool_result","content":"secret tool output"}]}}'
  echo '{"type":"user","message":{"content":"second question"}}'
  echo '{"type":"user","message":{"content":"third question"}}'
  echo '{"type":"user","message":{"content":"fourth question"}}'
} > "$f"

printf '{"session_id":"s1","transcript_path":"%s"}' "$f" \
  | CLAUDE_PLUGIN_DATA="$tmp" sh "$here/session-end.sh"

spool="$tmp/retain-queue/s1.txt"
[ -s "$spool" ] || { echo "FAIL: no spool written"; exit 1; }
grep -q 'decide: use Reactor' "$spool" || { echo "FAIL: user text missing"; exit 1; }
if grep -q 'tool_result\|secret tool output' "$spool"; then
  echo "FAIL: tool output leaked into the spool"; exit 1
fi

out=$(CLAUDE_PLUGIN_DATA="$tmp" sh "$here/session-start.sh")
printf '%s' "$out" | grep -q "$spool" || { echo "FAIL: start does not name the spool"; exit 1; }
printf '%s' "$out" | python3 -m json.tool >/dev/null || { echo "FAIL: start output is not JSON"; exit 1; }
echo "ok"
