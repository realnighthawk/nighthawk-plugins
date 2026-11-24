| Tool prefix | Use it for |
|---|---|
| `life__` | goals, tasks, routines, notes, and reminders |
| `finance__` | accounts, spending, budgets, and transactions |
| `maps__` | places, routes, distances, and weather |
| `retro__` | wardrobe, outfits, and saved looks |
| `health__` | health, fitness, and body records |
| `fpl__` | Fantasy Premier League data |
| `fpl-intelligence__` | FPL analysis, comparisons, and recommendations |
| `trek__` | trips, itineraries, bookings, packing and budgets |
| `gmail__`, `notion__` | the person's mail and Notion workspace |
| `browser__` | the person's own browser, on their workstation |
| `exa__`, `reddit__` | web search and Reddit |
| `grafana__` | dashboards, logs and metrics |

- Every service is reached through the one `shared` connection (the tenant's mcp-hub); a tool is named `<service>__<tool>`, and your harness may put its own prefix in front, so match by that ending and never invent a prefix. There is no other MCP server to call.
- Never invent a tool or argument: use the tools the connection advertises and their own schemas.
- `finance`, `maps`, `life`, and `retro` are scoped to the signed-in owner.
- If the connection is unavailable or unauthenticated, say so once and continue with what you have.
- If a tool is missing, blocked, or a call fails, try oh-my-pi's built-in browser before reporting it; it cannot replace a write the engine owns.
