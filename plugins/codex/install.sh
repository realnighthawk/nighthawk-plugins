#!/bin/sh
# Registers the Hippocampus MCP with Codex (OAuth) and adds the memory instructions to ~/.codex/AGENTS.md.
# Idempotent: each block is added once.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
cfg="${CODEX_HOME:-$HOME/.codex}"
mkdir -p "$cfg"
if ! grep -q '^\[mcp_servers\.hippocampus\]' "$cfg/config.toml" 2>/dev/null; then
  { printf '\n'; grep -v '^#' "$here/config.toml"; } >> "$cfg/config.toml"
  echo "added [mcp_servers.hippocampus] to $cfg/config.toml"
fi
if ! grep -q 'Long-term memory (Hippocampus)' "$cfg/AGENTS.md" 2>/dev/null; then
  { printf '\n'; cat "$here/AGENTS.md"; } >> "$cfg/AGENTS.md"
  echo "added memory instructions to $cfg/AGENTS.md"
fi
echo "next: codex mcp login hippocampus"
