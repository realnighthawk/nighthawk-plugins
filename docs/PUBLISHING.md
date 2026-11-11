# Publishing

The plugins ship as files in this public repo. There are no binaries, packages or images.

| Plugin | How it reaches users |
|---|---|
| `claude-code` | Claude marketplace in `.claude-plugin/marketplace.json`; bump the version in both `plugin.json` and `marketplace.json`, or cached installs keep the old one |
| `cursor` | Link or copy `plugins/cursor` into Cursor's local plugins folder |
| `codex` | `codex plugin marketplace add realnighthawk/nighthawk-plugins`, then `codex plugin add nighthawk-memory@nighthawk-plugins` and `codex mcp login hippocampus`; or `sh plugins/codex/install.sh` |
| `openclaw` | `openclaw plugins install --link ./plugins/openclaw` |

## App connectors (Claude apps, ChatGPT)

Only the memory server is published as a connector, never the hub. Connectors send a URL and an OAuth token but no custom header, so each has its own URL and the router pins `X-Agent-ID` from the path:

| Client | Connector URL | Agent / bank |
|---|---|---|
| Claude apps | `https://api.nighthawklabs.org/memory/mcp/claude-app` | `claude-app` |
| ChatGPT | `https://api.nighthawklabs.org/memory/mcp/chatgpt` | `chatgpt` |

Add yourself in Claude: Settings, Connectors, Add custom connector. The OAuth redirect `https://claude.ai/api/mcp/auth_callback` (and ChatGPT's) must be allowed on the Clerk application. Directory submission is separate: Claude through the Claude.ai developer portal, ChatGPT through the plugin submission portal. Both need the privacy policy URL (`https://mission-control.nighthawklabs.org/privacy`), a logo (`assets/nighthawk.svg`), and tool hints, which the memory server now declares.

## Release

Tag and create a GitHub release; there is no workflow:

```bash
git tag -a v0.4.0 -m "v0.4.0" && git push origin v0.4.0
gh release create v0.4.0 --generate-notes
```
