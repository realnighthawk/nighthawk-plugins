#!/bin/sh
# Runs the agent-brain-hook binary, downloading it from the GitHub release on first use.
# Fail-open: if the binary cannot be found or fetched, the hook does nothing and exits 0.
#
# Env: AGENT_BRAIN_HOOK_BIN      use this binary (development)
#      AGENT_BRAIN_HOOK_VERSION  release tag, default "latest"
#      AGENT_BRAIN_HOOK_REPO     default realnighthawk/agent-plugins
REPO="${AGENT_BRAIN_HOOK_REPO:-realnighthawk/agent-plugins}"
VERSION="${AGENT_BRAIN_HOOK_VERSION:-latest}"
DIR="${CLAUDE_PLUGIN_DATA:-${AGENT_BRAIN_STATE_DIR:-$HOME/.cache/agent-brain}}/bin"
BIN="${AGENT_BRAIN_HOOK_BIN:-$DIR/agent-brain-hook}"

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
