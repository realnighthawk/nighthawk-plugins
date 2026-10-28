---
description: Forget specific memories — shows what would be removed and waits for confirmation
argument-hint: <person, project, or fact to forget>
---

Target: $ARGUMENTS

Bank: !`printenv NIGHTHAWK_BANK || printenv AGENT_BRAIN_BANK || echo agent-harness`

1. `memory_recall` to find the exact payload text that holds this memory.
2. Show the user each exact payload and what forgetting it would remove, then
   wait for an explicit yes in this conversation.
3. Only after that confirmation, call `memory_forget` with the exact text or
   `payload_id`. Never call it speculatively, and never forget a broader set
   than the user confirmed.
