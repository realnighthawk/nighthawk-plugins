# Mission Control — Cursor plugin

Hippocampus long-term memory (`https://api.nighthawklabs.org/memory/mcp`) and the Reactor tool hub (`https://api.nighthawklabs.org/hub/mcp`) for Cursor.

| File | Does |
|---|---|
| `mcp.json` | Registers the `hippocampus` server (sends `X-Agent-ID: cursor`, so memory records Cursor as the speaker) and the `reactor` server. |
| `rules/hippocampus.mdc` | Always-on rule: recall before the first answer, retain what should outlive the session. |
| `skills/hippocampus/SKILL.md` | The tools and how to phrase a retain. |
| `rules/reactor.mdc`, `skills/reactor/SKILL.md` | Search the hub for a tool before concluding a capability is missing; the four entry tools. |

## Sign in

No key is stored. On first use Cursor opens the browser for OAuth (the same Clerk login as the Claude Code plugin). Approve it under Settings → MCP, once for `hippocampus` and once for `reactor`.

## Why a rule and not a hook

Cursor's `sessionStart` hook output is accepted, but injected context does not reliably reach the agent window (Cursor forum, 3.0.x). A rule always reaches it. The previous hook plugin called `memory_search`/`memory_write`, which no longer exist, so it was removed.

## One bank

Memory is one bank per agent: the `X-Agent-ID` header names the bank, so no call names a bank.
