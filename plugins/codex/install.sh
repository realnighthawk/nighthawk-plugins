#!/bin/sh
# Registers the Hippocampus and Reactor MCPs with Codex (OAuth) and adds the memory instructions to ~/.codex/AGENTS.md.
# Idempotent: each block is added once.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
cfg="${CODEX_HOME:-$HOME/.codex}"
mkdir -p "$cfg"
for name in hippocampus reactor; do
  if ! grep -q "^\[mcp_servers\.$name\]" "$cfg/config.toml" 2>/dev/null; then
    { printf '\n'; awk -v h="[mcp_servers.$name]" '/^\[/{on=($0==h)} on' "$here/config.toml"; } >> "$cfg/config.toml"
    echo "added [mcp_servers.$name] to $cfg/config.toml"
  fi
done
if ! grep -q 'Long-term memory (Hippocampus)' "$cfg/AGENTS.md" 2>/dev/null; then
  { printf '\n'; cat "$here/AGENTS.md"; } >> "$cfg/AGENTS.md"
  echo "added memory and Reactor instructions to $cfg/AGENTS.md"
fi
echo "next: codex mcp login hippocampus && codex mcp login reactor"
