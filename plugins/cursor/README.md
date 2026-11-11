# Nighthawk Memory — Cursor plugin

Long-term memory for Cursor through the Hippocampus MCP (`https://api.nighthawklabs.org/memory/mcp`).

| File | Does |
|---|---|
| `mcp.json` | Registers the `hippocampus` server. Sends `X-Agent-ID: cursor`, so memory records Cursor as the speaker. |
| `rules/hippocampus.mdc` | Always-on rule: recall before the first answer, retain what should outlive the session. |
| `skills/hippocampus/SKILL.md` | The tools and how to phrase a retain. |

## Sign in

No key is stored. On first use Cursor opens the browser for OAuth (the same Clerk login as the Claude Code plugin). Approve it under Settings → MCP → hippocampus.

## Why a rule and not a hook

Cursor's `sessionStart` hook output is accepted, but injected context does not reliably reach the agent window (Cursor forum, 3.0.x). A rule always reaches it. The previous hook plugin called `memory_search`/`memory_write`, which no longer exist, so it was removed.

## One bank

Memory is one bank per agent: the `X-Agent-ID` header names the bank, so a `bank_id` sent by this plugin is only a label.
