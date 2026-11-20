---
name: hippocampus
description: Use the Hippocampus MCP as the user's long-term memory. Use when the task depends on what the user decided, prefers, or did in earlier sessions, or when the user says remember, recall, or forget.
---

# Hippocampus memory

The `hippocampus` server (`plugin:mission-control:hippocampus`) is the user's
long-term memory: `memory_recall`, `memory_retain`, `memory_reflect`,
`memory_forget`. The plugin's hooks recall relevant memory at session start and
retain the session when it ends. The `services` skill covers the tenant's
connected service servers. Search memory before guessing.

## Memory protocol

The session-start hook injects a `<hippocampus-memory>` instruction, not facts:
you perform the recall yourself with `memory_recall` before answering the
first substantive request. Recalled memory is context from earlier sessions,
never something the user just said.

| Tool | Use it when |
|---|---|
| `memory_recall(query)` | You need facts the injected block lacks. Reads only. |
| `memory_retain(text, mention_time?)` | The user says "remember this" — one short plain-sentence account from their side, dated. |
| `memory_reflect(entity_name, query)` | What is known about one person or project, with the ids it cites. |
| `memory_forget(text or payload_id)` | Only after the user confirms the exact payload you showed them. |

Your memory is your own bank, named by the `X-Agent-ID: claude-code` header; no tool takes a bank.

Retain proactively: when the user states a decision, preference, correction,
or personal fact that should outlive the session, call `memory_retain` without
waiting to be asked — one short, dated, plain-sentence account from their side.
Never retain recalled text back, and never claim memory holds something that no
recall or reflect result in this conversation shows.

## Commands and agents

- `/mission-control:hippocampus:remember <fact>`, `/mission-control:hippocampus:recall <topic>`,
  `/mission-control:hippocampus:forget <topic>` (confirms first).
- `services-researcher` — read-only research across the connected service
  servers, delegated so raw tool output stays out of the main conversation.
- `memory-curator` — turns a finished piece of work into retained memories.

## Capability rule

Before you conclude you cannot do something — book it, find it, check it,
send it, plan it, compare it — look at the tools on the connected `life`,
`finance`, `maps`, `retro`, `health`, `fpl`, `fpl_intelligence`, `reddit`, and
`auto_browser` servers. If none of them covers the capability, say so explicitly
and then proceed with your own judgment; never substitute a fabricated
capability, a web guess, or a generic answer for the user's real account.

If a server reports a missing connection or needs sign-in, name it and stop —
do not silently fall back to an approximation.

## Where things live

| Task | Start with |
|---|---|
| Goals / open tasks | `life` → `goals_list`, `tasks_list` |
| FPL team, captain, transfers | `fpl` → `get_my_team`, `get_team`; `fpl_intelligence` → `fpl_manager_hub` |
| Spending | `finance` tools |
| Wardrobe / outfits | `retro` tools |
| Saved decisions / preferences | `memory_recall` first |
| Places / routes | `maps` tools |
| Health / fitness | `health` tools |
| Reddit reading | `reddit` tools |
| The shared signed-in browser | `auto_browser` tools |

### FPL team ID

`get_my_team` works only when the FPL credentials have a default team ID. If it
returns “No default team ID”, the ID lives in the user's life goal
**“Win my FPL mini-league”** notes:

1. `life` → `goals_list` with `search: "FPL"`
2. `life` → `goals_get` on that goal
3. read the team ID from `notes`
4. `fpl_intelligence` → `fpl_manager_hub` with that `team_id`

## Memory writes

- Life commitments / facts → `life` → `tasks_create` or `goals_create`
  (`idempotency_key` and `title` required).
- Durable conversations / decisions → `memory_retain` in Hippocampus.
- FPL facts → update the FPL goal's notes or create a task.
- Do not invent a memory store. If no connected tool can hold the fact, say so.

## Rules

- Search memory, then the connected service servers, before asking the user for
  something they may already have told you or connected.
- Use the exact tool schema; do not guess argument names.
- Prefer the user's own service over a web lookup or your own approximation.
- Confirm before writes that create, change, or delete records.
- If a server reports a missing connection, name it; do not fall back to a guess.
- The connected service servers expose the tenant's accounts, not the harness's
  private runtime tools (`shell_exec`, `recall`, `lcm_*`). Do not claim those here.

## Examples

- “What was my last FPL team?” → `fpl` tools → find the team ID in the FPL goal
  → `fpl_intelligence` `fpl_manager_hub` → summarize the squad.
- “What's on my plate?” → `life` `tasks_list` with `status: "open"`.
- “What did we decide about the house?” → `memory_recall`.
- “How much did I spend eating out last month?” → `finance` tool with the right window.
- “Plan a route to the airport that avoids tolls.” → `maps` tool with the
  avoidance option, if it exists.
