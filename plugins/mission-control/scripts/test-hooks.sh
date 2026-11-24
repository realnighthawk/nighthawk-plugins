#!/bin/sh
# One runnable check for the memory hooks: a stub memory server, a fabricated session; assert start recalls into JSON context and end retains the user
# text but never tool output, and that both do nothing without MC_MEMORY_TOKEN.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
tmp=$(mktemp -d)
trap 'kill "${srv:-}" 2>/dev/null || true; rm -rf "$tmp"' EXIT

TMP=$tmp python3 - <<'PY' &
import http.server, json, os
class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"])).decode()
        open(os.environ["TMP"] + "/seen", "a").write(self.path + " " + self.headers["Authorization"] + " " + body + "\n")
        out = {"results": [{"text": "prefers short answers"}]} if self.path.endswith("/recall") else {"ok": True}
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(json.dumps(out).encode())
    def log_message(self, *a): pass
s = http.server.HTTPServer(("127.0.0.1", 0), H)
open(os.environ["TMP"] + "/port", "w").write(str(s.server_port)); s.serve_forever()
PY
srv=$!
while [ ! -s "$tmp/port" ]; do sleep 0.1; done
export MC_MEMORY_URL=http://127.0.0.1:$(cat "$tmp/port") MC_MEMORY_BANK=t

f="$tmp/t.jsonl"
{
  echo '{"type":"user","message":{"content":"decide: keep the memory hooks"}}'
  echo '{"type":"assistant","message":{"content":[{"type":"text","text":"Agreed."}]}}'
  echo '{"type":"user","message":{"content":[{"type":"tool_result","content":"secret tool output"}]}}'
  echo '{"type":"user","message":{"content":"second"}}'; echo '{"type":"user","message":{"content":"third"}}'; echo '{"type":"user","message":{"content":"fourth"}}'
} > "$f"

# no token: silent no-op
[ -z "$(echo '{}' | sh "$here/session-start.sh")" ] || { echo "FAIL: start ran without a token"; exit 1; }
printf '{"transcript_path":"%s"}' "$f" | sh "$here/session-end.sh"; [ ! -e "$tmp/seen" ] || { echo "FAIL: end ran without a token"; exit 1; }

export MC_MEMORY_TOKEN=tok
out=$(echo '{}' | sh "$here/session-start.sh")
printf '%s' "$out" | python3 -c 'import json,sys;assert "prefers short answers" in json.load(sys.stdin)["hookSpecificOutput"]["additionalContext"]' || { echo "FAIL: recall not in context"; exit 1; }
printf '{"transcript_path":"%s","cwd":"/x/proj"}' "$f" | sh "$here/session-end.sh"
grep -q '/v1/default/banks/t/memories Bearer tok' "$tmp/seen" || { echo "FAIL: no retain call"; exit 1; }
grep -q 'keep the memory hooks' "$tmp/seen" || { echo "FAIL: user text not retained"; exit 1; }
! grep -q 'secret tool output' "$tmp/seen" || { echo "FAIL: tool output leaked"; exit 1; }
echo ok
