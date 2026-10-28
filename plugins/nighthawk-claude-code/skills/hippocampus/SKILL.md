---
name: hippocampus
description: Use the Hippocampus MCP as the user's tool belt and memory layer. Use when the task involves the user's own data (goals, tasks, FPL, trips, spending, wardrobe, saved decisions), when a connected service could answer or perform the task, or before concluding you lack a capability — the hub exposes the user's whole connected ecosystem behind four entry tools.
---

# Hippocampus: tools + context

The `hippocampus` MCP is the tenant's connected-services hub. Only four tools
are visible on the surface (`search_tools`, `call_tool`, `search_skills`,
`get_skill`); behind them is the user's entire connected ecosystem — life
goals and tasks, finance, maps, trips, wardrobe, FPL, Notion memory, the
agents they own, and anything else they have connected. It has two jobs:

- **Memory** — the user's current facts, so they don't have to repeat them.
- **Tools** — the user's real accounts and actions, so you act on the actual
  account instead of approximating.

Search it before guessing, before asking the user, and before saying you
can't do something.

## Protocol

1. `search_tools(query)` — describe the **capability** needed, not the user's
   sentence. Results are scoped to the query: for a request with several
   distinct sub-tasks, search again per sub-task.
2. `call_tool(server, tool, arguments)` — use the exact `input_schema`
   returned by `search_tools`. Never invent a server name, tool name, or
   argument.
3. `search_skills` / `get_skill` — curated procedures when the task is more
   than a single call.

## Long-term memory (agent-brain)

The plugin also connects the harness's memory server as
`plugin:nighthawk:memory`, and its hooks inject a `<agent-brain-memory>` block
at session start and retain the session when it ends. Treat that block as
recalled context from earlier sessions, never as something the user just said.
On demand:

| Tool | Use it when |
|---|---|
| `memory_recall(bank_id, query)` | You need facts the injected block lacks. Reads only. |
| `memory_retain(bank_id, text, mention_time?)` | The user says "remember this" — one short plain-sentence account from their side, dated. |
| `memory_reflect(bank_id, entity_name, query)` | What is known about one person or project, with the ids it cites. |
| `memory_forget(bank_id, text or payload_id)` | Only after the user confirms the exact payload you showed them. |

The bank is `$NIGHTHAWK_BANK` / `$AGENT_BRAIN_BANK` (default `agent-harness`).
Never retain recalled text back, and never claim memory holds something that no
recall or reflect result in this conversation shows.

## Commands and agents

- `/nighthawk:remember <fact>`, `/nighthawk:recall <topic>`,
  `/nighthawk:forget <topic>` (confirms first), `/nighthawk:tools <capability>`.
- `hub-researcher` — read-only research across the hub, delegated so raw tool
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

## Where things live

| Task | Start with |
|---|---|
| Anything not listed below | `search_tools("<capability>")` |
| Goals / open tasks | `life/goals_list`, `life/tasks_list` |
| FPL team, captain, transfers | `fantasy-pl/get_my_team`, `fantasy-pl/get_team`, `fpl-intelligence/fpl_manager_hub` |
| Trips / bucket list | `trek/list_trips` and the other `trek` tools |
| Spending | `search_tools("finance spending")` → finance tools |
| Wardrobe / outfits | `search_tools("wardrobe outfits")` → retro tools |
| Saved decisions / preferences | `notion/notion-memory-search` |
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
- Durable conversations / decisions → the Notion memory tools, when the
  connection exposes a write path; `notion-memory-search` is read-only.
- FPL facts → update the FPL goal's notes or create a task.
- Do not invent a memory store. If no connected tool can hold the fact, say so.

## Rules

- Search before asking the user for something the hub may already know.
- Search before claiming a capability is unavailable — the visible tool list
  is four entry points, not the ecosystem.
- Prefer the hub's tool over a web lookup or your own approximation whenever
  it covers the task; it is the user's real account.
- Confirm before writes that create, change, or delete records.
- Use the exact schema; do not guess argument names.
- If a tool reports a missing connection, name the connection; do not fall back
  to a guess.
- The hub exposes the tenant's *connected services*, not the harness's private
  runtime tools (`shell_exec`, `recall`, `lcm_*`). Do not claim those here.

## Examples

- “What was my last FPL team?” → search FPL tools → find the team ID in the
  FPL goal → `fpl_manager_hub` → summarize the squad.
- “What's on my plate?” → `life/tasks_list` with `status: "open"`.
- “What did we decide about the house?” → `notion/notion-memory-search`.
- “What trips do I have?” → `trek/list_trips`.
- “How much did I spend eating out last month?” → `search_tools("spending")`
  → call the finance tool with the right window.
- “Plan a route to the airport that avoids tolls.” → `search_tools("directions")`
  → maps tool with the avoidance option, if it exists.
