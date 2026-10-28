#!/bin/sh
# SessionStart signal: ask the agent to recall from Hippocampus memory using
# its own OAuth-authenticated MCP connection. This script only prints an
# instruction — it makes no network call and holds no credential.
[ -n "${NIGHTHAWK_DISABLE_HOOKS:-}" ] && exit 0
BANK="${NIGHTHAWK_BANK:-${AGENT_BRAIN_BANK:-agent-harness}}"
printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"<hippocampus-memory>\\nHippocampus memory is connected. Before answering the first request, call memory_recall on the Hippocampus MCP with bank_id \\"%s\\" and a short query about this project and the user, then use whatever is relevant. If the tool is unavailable or needs authentication, say so once and continue.\\n</hippocampus-memory>"}}\n' "$BANK"
