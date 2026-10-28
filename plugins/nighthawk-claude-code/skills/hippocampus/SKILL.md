---
name: hippocampus
description: Use the Hippocampus MCP as the user's living memory and the Reactor MCP as their tool belt. Use when the task involves the user's own data (goals, tasks, FPL, trips, spending, wardrobe, saved decisions), when a connected service could answer or perform the task, or before concluding you lack a capability — Reactor exposes the user's whole connected ecosystem behind four entry tools.
---

# Hippocampus memory, Reactor tools

Two servers, one layer:

- **Hippocampus** (`plugin:nighthawk:hippocampus`) — long-term memory:
  `memory_recall`, `memory_retain`, `memory_reflect`, `memory_forget`. The
  plugin's hooks recall relevant memory at session start and retain the session
  when it ends.
- **Reactor** (`plugin:nighthawk:reactor`) — the tenant's connected-services
  hub: four visible entry tools (`search_tools`, `call_tool`, `search_skills`,
  `get_skill`) with the user's entire connected ecosystem behind them — life
  goals and tasks, finance, maps, trips, wardrobe, FPL, Notion, the agents they
  own, and anything else they have connected.

Search memory before guessing, search Reactor before asking the user, and
search it before saying you can't do something.

## Reactor protocol

1. `search_tools(query)` — describe the **capability** needed, not the user's
   sentence. Results are scoped to the query: for a request with several
   distinct sub-tasks, search again per sub-task.
2. `call_tool(server, tool, arguments)` — use the exact `input_schema`
   returned by `search_tools`. Never invent a server name, tool name, or
   argument.
3. `search_skills` / `get_skill` — curated procedures when the task is more
   than a single call.

## Hippocampus memory

The session-start hook injects a `<hippocampus-memory>` instruction, not facts:
you perform the recall yourself with `memory_recall` before answering the
first substantive request. Recalled memory is context from earlier sessions,
never something the user just said.

| Tool | Use it when |
|---|---|
| `memory_recall(bank_id, query)` | You need facts the injected block lacks. Reads only. |
| `memory_retain(bank_id, text, mention_time?)` | The user says "remember this" — one short plain-sentence account from their side, dated. |
| `memory_reflect(bank_id, entity_name, query)` | What is known about one person or project, with the ids it cites. |
| `memory_forget(bank_id, text or payload_id)` | Only after the user confirms the exact payload you showed them. |

The bank is `$NIGHTHAWK_BANK` / `$AGENT_BRAIN_BANK` (default `agent-harness`).

Retain proactively: when the user states a decision, preference, correction,
or personal fact that should outlive the session, call `memory_retain` without
waiting to be asked — one short, dated, plain-sentence account from their side.
Never retain recalled text back, and never claim memory holds something that no
recall or reflect result in this conversation shows.

## Commands and agents

- `/nighthawk:remember <fact>`, `/nighthawk:recall <topic>`,
  `/nighthawk:forget <topic>` (confirms first), `/nighthawk:tools <capability>`.
- `hub-researcher` — read-only research across Reactor, delegated so raw tool
  output stays out of the main conversation.
- `memory-curator` — turns a finished piece of work into retained memories.

## Capability rule

Before you conclude you cannot do something — book it, find it, check it,
send it, plan it, compare it — call `search_tools` with a short description
of the capability. If it returns nothing relevant, say so explicitly and
then proceed with your own judgment; never substitute a fabricated
capability, a web guess, or a generic answer for the user's real account.

If a tool reports a missing connection, name the connection and stop — do
not silently fall back to an approximation.

## Where things live (Reactor)

| Task | Start with |
|---|---|
| Anything not listed below | `search_tools("<capability>")` |
| Goals / open tasks | `life/goals_list`, `life/tasks_list` |
| FPL team, captain, transfers | `fantasy-pl/get_my_team`, `fantasy-pl/get_team`, `fpl-intelligence/fpl_manager_hub` |
| Trips / bucket list | `trek/list_trips` and the other `trek` tools |
| Spending | `search_tools("finance spending")` → finance tools |
| Wardrobe / outfits | `search_tools("wardrobe outfits")` → retro tools |
| Saved decisions / preferences | `memory_recall` first; then `notion/notion-memory-search` |
| Places / routes | `search_tools("maps directions")` → maps-engine |

### FPL team ID

`get_my_team` works only when the FPL credentials have a default team ID. If it
returns “No default team ID”, the ID lives in the user's life goal
**“Win my FPL mini-league”** notes:

1. `life/goals_list` with `search: "FPL"`
2. `life/goals_get` on that goal
3. read the team ID from `notes`
4. `fpl-intelligence/fpl_manager_hub` with that `team_id`

## Memory writes

- Life commitments / facts → `life/tasks_create` or `life/goals_create`
  (`idempotency_key` and `title` required).
- Trip preferences → the relevant `trek` write tool.
- Durable conversations / decisions → `memory_retain` in Hippocampus; the
  Notion memory tools are the fallback when the user keeps older memories there.
- FPL facts → update the FPL goal's notes or create a task.
- Do not invent a memory store. If no connected tool can hold the fact, say so.

## Rules

- Search memory, then Reactor, before asking the user for something they may
  already have told you or connected.
- Search before claiming a capability is unavailable — the visible tool list
  is four entry points, not the ecosystem.
- Prefer Reactor's tool over a web lookup or your own approximation whenever
  it covers the task; it is the user's real account.
- Confirm before writes that create, change, or delete records.
- Use the exact schema; do not guess argument names.
- If a tool reports a missing connection, name the connection; do not fall back
  to a guess.
- Reactor exposes the tenant's *connected services*, not the harness's private
  runtime tools (`shell_exec`, `recall`, `lcm_*`). Do not claim those here.

## Examples

- “What was my last FPL team?” → search FPL tools → find the team ID in the
  FPL goal → `fpl_manager_hub` → summarize the squad.
- “What's on my plate?” → `life/tasks_list` with `status: "open"`.
- “What did we decide about the house?” → `memory_recall`, then
  `notion/notion-memory-search` if memory is thin.
- “What trips do I have?” → `trek/list_trips`.
- “How much did I spend eating out last month?” → `search_tools("spending")`
  → call the finance tool with the right window.
- “Plan a route to the airport that avoids tolls.” → `search_tools("directions")`
  → maps tool with the avoidance option, if it exists.
