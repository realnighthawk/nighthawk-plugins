# Mission Control for Claude

Mission Control gives Claude a long-term memory that survives between conversations: it recalls
what the user decided or prefers before answering, retains decisions, preferences and corrections
worth keeping, and forgets something only after the user confirms the exact entry.

The hosted connector is memory-only; the user's connected services are not reachable from here.

## What is in it

| Part | What it does |
|---|---|
| `hippocampus` connector and skill | Long-term memory, through `https://api.nighthawklabs.org/memory/mcp/claude-app`. |

## What it connects to and sends

The plugin runs no code and has no hooks. It declares one remote MCP server over HTTPS, signed in
with OAuth, so no key is stored in the plugin. Memory is a separate bank per agent, named by the
connector path, so what Claude remembers is kept apart from other agents. What Claude retains is
only what the user states in conversation; recalled memory is never written back.

## Privacy and licence

Privacy policy: https://mission-control.nighthawklabs.org/privacy. MIT licensed, see the repository `LICENSE`.
