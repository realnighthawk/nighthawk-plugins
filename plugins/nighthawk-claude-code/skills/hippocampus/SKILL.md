---
name: hippocampus
description: Use the Hippocampus MCP as the user's living context and memory layer. Use when the user asks about their own data — goals, tasks, FPL team, trips, spending, wardrobe, saved decisions — or asks what you know/remember about them. Also use at the start of a session when personal context would change the answer.
---

# Hippocampus context layer

The `hippocampus` MCP is the tenant's connected-services hub. It is where the
user's current facts live: goals and tasks, FPL, trips, spending, wardrobe,
places, Notion memories, and the rest of the tenant's connected ecosystem.
Search it before guessing or asking the user to repeat themselves.

## Protocol

1. `search_tools(query)` — search by **capability**, not by the user's sentence.
2. `call_tool(server, tool, arguments)` — use the exact `input_schema` returned
   by `search_tools`.
3. `search_skills` / `get_skill` for curated procedures.

Never claim a stored fact unless a tool result in this conversation shows it.

## Where things live

| Question | Start with |
|---|---|
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
