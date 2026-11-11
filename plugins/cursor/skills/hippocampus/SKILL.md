---
name: hippocampus
description: Use the Hippocampus MCP as the user's long-term memory. Use when the task depends on what the user decided, prefers, or did in earlier sessions, or when the user says remember, recall, or forget.
---

# Hippocampus memory

One bank per user. The server pins the bank, so `bank_id` is just a label; pass "nighthawk". Your calls are recorded as the agent `cursor` (the `X-Agent-ID` header in `mcp.json`), so what you did and what the user said stay distinguishable.

| Tool | Use it when |
|---|---|
| `memory_recall(bank_id, query)` | You need facts from earlier sessions. Reads only. |
| `memory_retain(bank_id, text, mention_time?)` | The user says "remember this", or states a decision, preference or correction. One short dated plain-sentence account. |
| `memory_reflect(bank_id, entity_name, query)` | What is known about one person or project, with the ids it cites. |
| `memory_forget(bank_id, text or payload_id)` | Only after the user confirms the exact payload you showed them. |

Write "the user" for the person and "cursor" for yourself, so facts attach to the right entities. Retain facts from the user's side; do not retain recalled text, and never claim memory holds something no recall result shows.
