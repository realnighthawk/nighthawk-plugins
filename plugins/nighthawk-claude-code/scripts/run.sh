#!/bin/sh
# Hippocampus memory hooks: recall long-term memory at session start, retain the
# session when it ends. Runs agent-brain-hook — the memory hook binary released
# with this repo — downloading it from GitHub Releases on first use and caching
# it in the plugin data directory. Fail-open: if the binary cannot be found or
# fetched, the hook exits 0 and does nothing.
#
# Settings come from NIGHTHAWK_* variables (AGENT_BRAIN_* are also accepted) or a
# KEY=VALUE file:
#   NIGHTHAWK_MCP_URL   streamable-HTTP URL of the memory server
#   NIGHTHAWK_API_KEY   sent as X-API-Key
#   NIGHTHAWK_BANK      memory bank name
# Config file: $NIGHTHAWK_CONFIG, else ~/.config/nighthawk/plugin.env, else
# ~/.config/agent-brain/plugin.env.
#
# Developer knobs: NIGHTHAWK_HOOK_BIN (binary to run), NIGHTHAWK_HOOK_VERSION
# (release tag, default "latest"), NIGHTHAWK_HOOK_REPO.

REPO="${NIGHTHAWK_HOOK_REPO:-realnighthawk/nighthawk-plugins}"
VERSION="${NIGHTHAWK_HOOK_VERSION:-latest}"
STATE="${NIGHTHAWK_STATE_DIR:-${CLAUDE_PLUGIN_DATA:-$HOME/.cache/nighthawk}}"
DIR="$STATE/bin"
BIN="${NIGHTHAWK_HOOK_BIN:-$DIR/agent-brain-hook}"

# The binary reads AGENT_BRAIN_*; a NIGHTHAWK_* value wins when set.
copy() { v=$(printenv "$1" 2>/dev/null) || v=""; [ -n "$v" ] && export "$2=$v"; return 0; }
copy NIGHTHAWK_MCP_URL AGENT_BRAIN_MCP_URL
copy NIGHTHAWK_API_KEY AGENT_BRAIN_API_KEY
copy NIGHTHAWK_BANK AGENT_BRAIN_BANK
copy NIGHTHAWK_DISABLE_HOOKS AGENT_BRAIN_DISABLE_HOOKS
export AGENT_BRAIN_STATE_DIR="$STATE"

if [ -n "${NIGHTHAWK_CONFIG:-}" ]; then
  export AGENT_BRAIN_CONFIG="$NIGHTHAWK_CONFIG"
elif [ -f "$HOME/.config/nighthawk/plugin.env" ]; then
  export AGENT_BRAIN_CONFIG="$HOME/.config/nighthawk/plugin.env"
elif [ -f "$HOME/.config/agent-brain/plugin.env" ]; then
  export AGENT_BRAIN_CONFIG="$HOME/.config/agent-brain/plugin.env"
fi

fetch() {
  case "$(uname -s)" in Darwin) os=darwin ;; Linux) os=linux ;; *) return 1 ;; esac
  case "$(uname -m)" in x86_64 | amd64) arch=amd64 ;; arm64 | aarch64) arch=arm64 ;; *) return 1 ;; esac
  if [ "$VERSION" = latest ]; then base="https://github.com/$REPO/releases/latest/download"
  else base="https://github.com/$REPO/releases/download/$VERSION"; fi
  asset="agent-brain-hook-$os-$arch"
  tmp="$(mktemp -d)" || return 1
  curl -fsSL --max-time 20 -o "$tmp/$asset" "$base/$asset" && curl -fsSL --max-time 10 -o "$tmp/checksums.txt" "$base/checksums.txt" || { rm -rf "$tmp"; return 1; }
  want="$(grep " $asset\$" "$tmp/checksums.txt" | awk '{print $1}')"
  got="$( (sha256sum "$tmp/$asset" 2>/dev/null || shasum -a 256 "$tmp/$asset") | awk '{print $1}')"
  if [ -z "$want" ] || [ "$want" != "$got" ]; then rm -rf "$tmp"; return 1; fi
  mkdir -p "$DIR" && chmod +x "$tmp/$asset" && mv "$tmp/$asset" "$BIN"
  rm -rf "$tmp"
}

[ -x "$BIN" ] || fetch 2>/dev/null
[ -x "$BIN" ] || exit 0
exec "$BIN" "$@"
