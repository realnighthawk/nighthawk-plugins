# Mission Control for Claude

Mission Control gives Claude two things it does not have on its own: a long-term memory that survives between conversations, and access to the services the user has connected to their own Mission Control account.

## What is in it

| Part | What it does |
|---|---|
| `hippocampus` connector and skill | Long-term memory. Claude recalls what the user decided or prefers before answering, retains decisions, preferences and corrections worth keeping, and forgets something only after the user confirms the exact entry. |
| `reactor` connector and skill | The user's tool hub. Claude searches it for a connected service (maps, finance, trips, tasks, Notion and more) before saying it cannot do something, then calls the tool it found. |

## What it connects to and sends

The plugin runs no code and has no hooks. It declares two remote MCP servers over HTTPS, `https://api.nighthawklabs.org/memory/mcp/claude-app` and `https://api.nighthawklabs.org/hub/mcp`. Both sign the user in with OAuth, so no key is stored in the plugin. Memory is a separate bank per agent, named by the connector path, so what Claude app remembers is kept apart from other agents. What Claude retains is only what the user states in conversation; recalled memory is never written back.

## Privacy and licence

Privacy policy: https://mission-control.nighthawklabs.org/privacy. MIT licensed, see the repository `LICENSE`.
