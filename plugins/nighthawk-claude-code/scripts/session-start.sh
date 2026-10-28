#!/bin/sh
# SessionStart signal: ask the agent to recall through its own
# OAuth-authenticated MCP connection, and to retain any session slice the
# previous SessionEnd spooled. This script only prints an instruction — it
# makes no network call and holds no credential.
[ -n "${NIGHTHAWK_DISABLE_HOOKS:-}" ] && exit 0
BANK="${NIGHTHAWK_BANK:-${AGENT_BRAIN_BANK:-agent-harness}}"

dir="${CLAUDE_PLUGIN_DATA:-$HOME/.cache/nighthawk}/retain-queue"
deferred=""
n=0
for f in "$dir"/*.txt; do
  [ -f "$f" ] || continue
  deferred="$deferred\\n  - $f"
  n=$((n + 1))
  [ "$n" -ge 5 ] && break
done
if [ -n "$deferred" ]; then
  extra="\\n 2. Retain the deferred session slices below first: for each path, delegate to the nighthawk:memory-curator subagent with bank_id \\\"$BANK\\\" and that path, then delete the file with rm.\\nDeferred:$deferred"
else
  extra=""
fi

printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"<hippocampus-memory>\\nHippocampus memory is connected. Before answering the first request:\\n 1. call memory_recall on the Hippocampus MCP with bank_id \\"%s\\" and a short query about this project and the user; if the tool is unavailable or needs authentication, say so once and continue.%s\\n</hippocampus-memory>"}}\n' "$BANK" "$extra"
