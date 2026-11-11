# Publishing

The plugins ship as files in this public repo. There are no binaries, packages or images.

| Plugin | How it reaches users |
|---|---|
| `claude-code` | Claude marketplace in `.claude-plugin/marketplace.json`; bump the version in both `plugin.json` and `marketplace.json`, or cached installs keep the old one |
| `cursor` | Link or copy `plugins/cursor` into Cursor's local plugins folder |
| `codex` | `codex plugin marketplace add realnighthawk/nighthawk-plugins`, then `codex plugin add mission-control@mission-control-plugins` and `codex mcp login hippocampus`; or `sh plugins/codex/install.sh` |
| `openclaw` | `openclaw plugins install --link ./plugins/openclaw` |

## App connectors (Claude apps, ChatGPT)

Both servers are connectors in both apps: Hippocampus (memory) and Reactor (the tool hub). Connectors send a URL and an OAuth token but no custom header, so each memory connector has its own URL and the router pins `X-Agent-ID` from the path. The hub needs no agent, so both apps share its URL.

| Connector | Claude apps | ChatGPT | Agent / bank |
|---|---|---|---|
| Hippocampus | `https://api.nighthawklabs.org/memory/mcp/claude-app` | `https://api.nighthawklabs.org/memory/mcp/chatgpt` | `claude-app` / `chatgpt` |
| Reactor | `https://api.nighthawklabs.org/hub/mcp` | `https://api.nighthawklabs.org/hub/mcp` | none |

Add yourself in Claude: Settings, Connectors, Add custom connector, once per URL. The OAuth redirect `https://claude.ai/api/mcp/auth_callback` (and ChatGPT's) must be allowed on the Clerk application. Directory submission is separate and is one submission per server: Claude through the Claude.ai developer portal, ChatGPT through the plugin submission portal. Each needs the privacy policy URL (`https://mission-control.nighthawklabs.org/privacy`), a logo (`assets/mission-control.svg`), and tool hints, which both servers declare (memory in `agent-brain`, the hub in `infra/mcp-hub`). `call_tool` is declared destructive and open-world because it proxies arbitrary backend tools, so expect reviewers to ask about it.

## Store listings: one "Mission Control" in each store

One listing per store holds both servers and both skills. Each store also takes the two servers as separate connectors, which is why the listing points at the same URLs.

| Store | Folder | Submit as |
|---|---|---|
| Claude directory | `plugins/claude-app` | Plugin bundle from this public repo (`claude plugin validate plugins/claude-app` passes), plus each server as an MCP connector so the two listings pair. No hooks or commands, because command hooks are held for a reviewer until the org is Verified. |
| ChatGPT | `plugins/chatgpt` | ZIP of the folder (`cd plugins/chatgpt && zip -r ../mission-control-chatgpt.zip .`) uploaded at Plugins, Upload new or existing plugin. Uses the Codex package layout the portal expects (`.codex-plugin/plugin.json`, `.mcp.json`, `skills/`, `assets/`); a root `plugin.json` is rejected. Declares both MCP servers and ships both skills. The portal docs say a plugin can declare several servers but only one can be connected, so check whether both are usable in one listing. |

Still to do before submitting to ChatGPT, none of which is in the repo:
- Verified publisher identity. `supportURL` and `termsOfServiceURL` are set in `plugins/chatgpt/plugin.json` (`/support` and `/terms` on mission-control.nighthawklabs.org).
- OAuth settings for each server on the portal's MCPs step, and domain verification: serve the portal's token as plain text at `https://api.nighthawklabs.org/.well-known/openai-apps-challenge`.
- Five positive and three negative test cases, a reviewer video, release notes, and a test account.

## Release

Tag and create a GitHub release; there is no workflow:

```bash
git tag -a v0.4.0 -m "v0.4.0" && git push origin v0.4.0
gh release create v0.4.0 --generate-notes
```
