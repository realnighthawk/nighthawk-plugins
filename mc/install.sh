#!/bin/sh
# Installs mc, which runs omp with your Mission Control workstation's browser attached.
#   curl -fsSL https://raw.githubusercontent.com/realnighthawk/nighthawk-plugins/main/mc/install.sh | sh
set -eu
BIN=${MC_BIN_DIR:-$HOME/.local/bin}
SRC=${MC_SRC:-https://raw.githubusercontent.com/realnighthawk/nighthawk-plugins/main/mc/mc}
mkdir -p "$BIN"
curl -fsSL "$SRC" -o "$BIN/mc"
chmod +x "$BIN/mc"
echo "installed $BIN/mc"
if ! command -v websocat >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    echo "installing websocat with brew"; brew install websocat
  else
    echo "websocat is also needed: https://github.com/vi/websocat#installation"
  fi
fi
case ":$PATH:" in *":$BIN:"*) ;; *) echo "add $BIN to your PATH" ;; esac
echo "then run: mc omp"
