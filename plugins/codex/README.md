# Mission Control — Codex

Hippocampus long-term memory and the Reactor tool hub for Codex, both signed in with OAuth.

**As a plugin** (marketplace manifest: `.agents/plugins/marketplace.json` at the repo root):

```sh
codex plugin marketplace add realnighthawk/nighthawk-plugins   # leave sparse paths empty
codex plugin add mission-control@mission-control-plugins
codex mcp login hippocampus                                    # browser OAuth, no key stored
codex mcp login reactor
```

**Without the plugin:** `sh plugins/codex/install.sh` writes the `config.toml` entry and `AGENTS.md` instructions, then `codex mcp login hippocampus` and `codex mcp login reactor`.

`http_headers = { "X-Agent-ID" = "codex" }` makes memory record Codex as the speaker. Memory is one bank per agent, named by that header; no call names a bank. Recall is a skill (`skills/hippocampus`) in the plugin and an `AGENTS.md` block in the manual install; `skills/reactor` and the same `AGENTS.md` cover the hub.
