| Server | Use it for |
|---|---|
| `life` | goals, tasks, routines, notes, and reminders |
| `finance` | accounts, spending, budgets, and transactions |
| `maps` | places, routes, distances, and weather |
| `retro` | wardrobe, outfits, and saved looks |
| `health` | health, fitness, and body records |
| `fpl` | Fantasy Premier League data |
| `fpl_intelligence` | FPL analysis, comparisons, and recommendations |
| `reddit` | Reddit search and reading |
| `auto_browser` | the shared signed-in browser |

- Call a server's tools directly. There is no hub to search and no entry tool to go through.
- Never invent a server, tool, or argument: use the tools the server advertises and their own schemas.
- `finance`, `maps`, `life`, and `retro` are scoped to the signed-in owner; `auto_browser` drives the shared browser session.
- If a server is unavailable or unauthenticated, say so once and continue with what you have.
