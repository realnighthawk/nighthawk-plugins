---
description: Recall what long-term memory holds about a topic
argument-hint: <topic or question>
---

Question: $ARGUMENTS

Bank: !`printenv NIGHTHAWK_BANK || printenv AGENT_BRAIN_BANK || echo agent-harness`

1. `memory_recall` with the bank and a tight query for the topic.
2. If the answer could equally live in a connected service (goals, tasks,
   trips, spending, FPL, Notion), also `search_tools` → `call_tool` on the
   Hippocampus hub.
3. Answer only from what the results show, and name where each fact came from
   (memory, life, trek, ...). If nothing is there, say that plainly instead of
   guessing.
