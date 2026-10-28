# Nighthawk: Claude Code plugin

Connects Claude Code to the agent harness MCP endpoint at
`https://api.nighthawklabs.org/hub/mcp` — the tenant's agents, tools, memory,
and connected services (maps, finance, life, retro, and anything else
connected through the tenant's mcp-hub). The URL is fixed; there is no
environment variable to set.

Authentication is Claude Code's native MCP OAuth flow. There is no token to
copy and no secret in this plugin: `/mcp` opens the Clerk consent screen,
stores the tokens in the OS keychain, and refreshes them automatically.

## Context / memory skill

The plugin ships the `hippocampus` skill (`nighthawk:hippocampus`). It teaches
Claude Code to search the MCP for the user's goals, tasks, FPL team, trips,
spending, and saved decisions before asking or guessing. It loads
automatically when a question is about the user's own data.

## Install

```bash
claude plugin marketplace add realnighthawk/nighthawk-plugins --scope user
claude plugin install nighthawk@nighthawk-plugins --scope user
```

Then open `/mcp`, select `plugin:nighthawk:hippocampus`, and authenticate. The
server's tools appear as `mcp__plugin_nighthawk_hippocampus__*`.

For SSH/headless sessions:

```bash
claude mcp login plugin:nighthawk:hippocampus --no-browser
```

(`claude -p` and Agent SDK runs cannot complete OAuth; authenticate once in an
interactive session first.)

## Configuration

The endpoint is fixed at `https://api.nighthawklabs.org/hub/mcp`. Do not add
an `Authorization` header or `headersHelper` for this server — either
disables Claude Code's OAuth fallback.

## Server prerequisites

The harness router must serve the MCP OAuth discovery documents
(`/.well-known/oauth-protected-resource` and
`/.well-known/oauth-authorization-server`) and Clerk must have CIMD
(preferred) or DCR enabled for the OAuth application, with default scopes
`openid profile email offline_access`.

## Remove

```bash
claude plugin uninstall nighthawk@nighthawk-plugins --scope user
```

Uninstalling also removes the stored OAuth credentials for the endpoint.
