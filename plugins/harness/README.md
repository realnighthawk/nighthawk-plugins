# Agent Harness: Claude Code plugin

Connects Claude Code to the agent harness MCP endpoint at
`https://api.nighthawklabs.org/hub/mcp` — the tenant's agents, tools, memory,
and connected services (maps, finance, life, retro, and anything else
connected through the tenant's mcp-hub).

Authentication is Claude Code's native MCP OAuth flow. There is no token to
copy and no secret in this plugin: `/mcp` opens the Clerk consent screen,
stores the tokens in the OS keychain, and refreshes them automatically.

## Install

```bash
claude plugin marketplace add realnighthawk/agent-plugins --scope user
claude plugin install harness@agent-plugins --scope user
```

Then open `/mcp`, select `plugin:harness:harness`, and authenticate. The
server's tools appear as `mcp__plugin_harness_harness__*`.

For SSH/headless sessions:

```bash
claude mcp login plugin:harness:harness --no-browser
```

(`claude -p` and Agent SDK runs cannot complete OAuth; authenticate once in an
interactive session first.)

## Configuration

The endpoint defaults to `https://api.nighthawklabs.org/hub/mcp`. Override it
with `HARNESS_MCP_URL` for another deployment. Do not add an
`Authorization` header or `headersHelper` for this server — either disables
Claude Code's OAuth fallback.

## Server prerequisites

The harness router must serve the MCP OAuth discovery documents
(`/.well-known/oauth-protected-resource` and
`/.well-known/oauth-authorization-server`) and Clerk must have CIMD
(preferred) or DCR enabled for the OAuth application, with default scopes
`openid profile email offline_access`.

## Remove

```bash
claude plugin uninstall harness@agent-plugins --scope user
```

Uninstalling also removes the stored OAuth credentials for the endpoint.
