# Nighthawk Memory — Codex

Long-term memory for Codex through the Hippocampus MCP, signed in with OAuth.

**As a plugin** (marketplace manifest: `.agents/plugins/marketplace.json` at the repo root):

```sh
codex plugin marketplace add realnighthawk/nighthawk-plugins   # leave sparse paths empty
codex plugin add nighthawk-memory@nighthawk-plugins
codex mcp login hippocampus                                    # browser OAuth, no key stored
```

**Without the plugin:** `sh plugins/codex/install.sh` writes the `config.toml` entry and `AGENTS.md` instructions, then `codex mcp login hippocampus`.

`http_headers = { "X-Agent-ID" = "codex" }` makes memory record Codex as the speaker. Memory is one bank per agent, named by that header; no call names a bank. Recall is a skill (`skills/hippocampus`) in the plugin and an `AGENTS.md` block in the manual install.
