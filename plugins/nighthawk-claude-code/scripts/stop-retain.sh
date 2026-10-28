#!/bin/sh
# Stop signal, at most once per substantial session: ask the agent to retain
# durable memory through its own OAuth-authenticated MCP connection before it
# finishes. This script only prints an instruction — no network, no credential.
[ -n "${NIGHTHAWK_DISABLE_HOOKS:-}" ] && exit 0

event=$(cat)

# Already continuing because of a stop hook: let the agent stop.
printf '%s' "$event" | grep -q '"stop_hook_active":[[:space:]]*true' && exit 0

field() { printf '%s' "$event" | sed -n "s/.*\"$1\":[[:space:]]*\"\([^\"]*\)\".*/\1/p"; }
session=$(field session_id)
transcript=$(field transcript_path)
[ -n "$transcript" ] && [ -f "$transcript" ] || exit 0

# Substantial sessions only: 4+ user turns or 4 KB of transcript.
turns=$(grep -c '"type":"user"' "$transcript" 2>/dev/null) || true
[ -n "$turns" ] || turns=0
size=$(wc -c < "$transcript" 2>/dev/null | tr -d ' ')
[ "$turns" -ge 4 ] 2>/dev/null || [ "${size:-0}" -ge 4000 ] 2>/dev/null || exit 0

# At most one signal per session.
state="${CLAUDE_PLUGIN_DATA:-$HOME/.cache/nighthawk}/retain"
mkdir -p "$state" 2>/dev/null || exit 0
key=$(printf '%s' "${session:-no-session}" | tr -c 'A-Za-z0-9_-' '_')
[ -f "$state/$key" ] && exit 0
: > "$state/$key"

BANK="${NIGHTHAWK_BANK:-${AGENT_BRAIN_BANK:-agent-harness}}"
printf '{"decision":"block","reason":"<hippocampus-memory>Before you finish: retain the durable decisions, preferences, corrections, and personal facts from this session with memory_retain on the Hippocampus MCP (bank_id \\"%s\\"), one short dated sentence each. Skip routine or transient details and never retain recalled text. If nothing is durable, stop normally.</hippocampus-memory>"}\n' "$BANK"
