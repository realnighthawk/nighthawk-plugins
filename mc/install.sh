#!/bin/sh
# One step to set up Mission Control for omp: installs websocat and mc, adds the Mission Control plugin to omp, and signs you in.
#   curl -fsSL https://raw.githubusercontent.com/realnighthawk/nighthawk-plugins/main/mc/install.sh | sh
# Safe to run again: it updates what is there. Nothing needs sudo; programs go in ~/.local/bin.
# MC_NO_LOGIN=1 skips the sign-in at the end.
set -eu
BIN=${MC_BIN_DIR:-$HOME/.local/bin}
SRC=${MC_SRC:-https://raw.githubusercontent.com/realnighthawk/nighthawk-plugins/main/mc/mc}
MARKETPLACE=mission-control-plugins
MARKET_URL=https://github.com/realnighthawk/nighthawk-plugins.git
PLUGIN=mission-control@$MARKETPLACE

step() { printf '\n==> %s\n' "$*"; }
mkdir -p "$BIN"
PATH="$BIN:$PATH"; export PATH

step "websocat (connects omp's browser to your workstation)"
if command -v websocat >/dev/null 2>&1; then
  echo "already installed: $(command -v websocat)"
else
  case "$(uname -s)-$(uname -m)" in
    Darwin-arm64) asset=aarch64-apple-darwin ;;
    Darwin-x86_64) asset=x86_64-apple-darwin ;;
    Linux-x86_64) asset=x86_64-unknown-linux-musl ;;
    Linux-aarch64 | Linux-arm64) asset=aarch64-unknown-linux-musl ;;
    *) echo "no websocat build for $(uname -s) $(uname -m): see https://github.com/vi/websocat" >&2; exit 1 ;;
  esac
  curl -fsSL "https://github.com/vi/websocat/releases/latest/download/websocat.$asset" -o "$BIN/websocat"
  chmod +x "$BIN/websocat"
  echo "installed $BIN/websocat"
fi

step "mc"
curl -fsSL "$SRC" -o "$BIN/mc"
chmod +x "$BIN/mc"
echo "installed $BIN/mc"

step "the Mission Control plugin for omp"
if ! command -v omp >/dev/null 2>&1; then
  echo "omp is not installed, so the plugin was skipped. Install oh-my-pi, then run this again." >&2
else
  # omp exits 0 even when a step fails, so read what it says.
  run() { out=$("$@" 2>&1) || true; printf '%s\n' "$out"; case $out in *"Failed"* | *"failed"* | *"rror"*) return 1 ;; esac; }
  if omp plugin marketplace list 2>&1 | grep -q "$MARKETPLACE"; then run omp plugin marketplace update "$MARKETPLACE"; else run omp plugin marketplace add "$MARKET_URL"; fi
  if omp plugin list 2>&1 | grep -q "$PLUGIN"; then run omp plugin upgrade "$PLUGIN"; else run omp plugin install "$PLUGIN"; fi
fi

# A program in ~/.local/bin is only found if that directory is on the PATH.
profile=
case "${SHELL:-}" in */zsh) profile=$HOME/.zshrc ;; */bash) profile=$HOME/.bashrc ;; esac
if [ -n "$profile" ] && ! grep -q '\.local/bin' "$profile" 2>/dev/null; then
  printf '\nexport PATH="$HOME/.local/bin:$PATH"\n' >>"$profile"
  echo "added ~/.local/bin to your PATH in $profile (open a new terminal to use it)"
fi

if [ -z "${MC_NO_LOGIN:-}" ]; then
  step "sign in"
  "$BIN/mc" login || echo "sign in later with: mc login"
fi

printf '\nDone. Start omp with your workstation attached:  mc omp\n'
