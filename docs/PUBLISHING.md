# Publishing

The plugins ship as files in this public repo. There are no binaries or images.

| Plugin | How it reaches users |
|---|---|
| `mission-control` (Claude Code, oh-my-pi) | Claude marketplace in `.claude-plugin/marketplace.json`; oh-my-pi marketplace in `.omp-plugin/marketplace.json`; both source `./plugins/mission-control`. Bump the version in `.claude-plugin/plugin.json`, `plugin.json` and both marketplace entries, or cached installs keep the old one |
| `claude-app` | Claude app connector, memory only |
| `chatgpt-memory` | ChatGPT app connector, memory only |

## App connectors (Claude apps, ChatGPT)

Both apps carry Hippocampus memory only; the tenant's service servers are not reachable from the hosted connectors. Connectors send a URL and an OAuth token but no custom header, so each memory connector has its own URL and the router pins `X-Agent-ID` from the path.

| Connector | Claude apps | ChatGPT |
|---|---|---|
| Hippocampus | `https://api.nighthawklabs.org/memory/mcp/claude-app` | `https://api.nighthawklabs.org/memory/mcp/chatgpt` |

Add yourself in Claude: Settings, Connectors, Add custom connector. The OAuth redirect `https://claude.ai/api/mcp/auth_callback` (and ChatGPT's) must be allowed on the Clerk application. Directory submission is separate: Claude through the Claude.ai developer portal, ChatGPT through the plugin submission portal. Each needs the privacy policy URL (`https://mission-control.nighthawklabs.org/privacy`) and a logo (`assets/mission-control.svg`).

For ChatGPT, upload `plugins/chatgpt-memory` as a ZIP (`cd plugins/chatgpt-memory && zip -r ../mission-control-memory.zip .`). The layout is the OpenAI plugin layout the portal requires (`.codex-plugin/plugin.json`, `.mcp.json`, `skills/`, `assets/`); the five positive and three negative test cases are in the manifest under `extensions.com.openai.review.test_cases`.

## Store listings: one "Mission Control Memory" in each store

| Store | Folder | Submit as |
|---|---|---|
| Claude directory | `plugins/claude-app` | Plugin bundle from this public repo (`claude plugin validate plugins/claude-app` passes), plus the memory server as an MCP connector. No hooks or commands, because command hooks are held for a reviewer until the org is Verified. |
| ChatGPT | `plugins/chatgpt-memory` | ZIP of the folder (`cd plugins/chatgpt-memory && zip -r ../mission-control-memory.zip .`) uploaded at Plugins, Upload new or existing plugin. Uses the OpenAI plugin layout the portal expects (`.codex-plugin/plugin.json`, `.mcp.json`, `skills/`, `assets/`); a root `plugin.json` is rejected. |

Still to do before submitting to ChatGPT, none of which is in the repo (the demo video URL goes in each manifest as `extensions.com.openai.review.demo_recording_url`):
- Verified publisher identity. `supportURL` and `termsOfServiceURL` are set in `plugins/chatgpt-memory/plugin.json` (`/support` and `/terms` on mission-control.nighthawklabs.org).
- OAuth settings for each server on the portal's MCPs step, and domain verification: serve the portal's token as plain text at `https://api.nighthawklabs.org/.well-known/openai-apps-challenge`.
- Five positive and three negative test cases, a reviewer video, release notes, and a test account.

## Release

Plugins and the installer package have separate tags in one repository.

```bash
# plugins: tag the release
git tag -a v0.13.0 -m "v0.13.0" && git push origin v0.13.0
gh release create v0.13.0 --generate-notes
```

`@nighthawklabs/mission-control` (`packages/mission-control`, tag `mission-control-vX.Y.Z` matching its package.json) bundles `mc/mc` and `mc/install.sh` at pack time, so `npx` runs the starter that was published.

`.github/workflows/npm-publish.yml` publishes `@nighthawklabs/mission-control` on its tag; plugin tags do not publish npm.
