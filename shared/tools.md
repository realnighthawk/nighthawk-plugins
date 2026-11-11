| Tool | Use it when |
|---|---|
| `memory_recall(bank_id, query)` | You need facts from earlier sessions. Reads only. |
| `memory_retain(bank_id, text, mention_time?)` | The user says "remember this", or states a decision, preference or correction. One short dated plain-sentence account. |
| `memory_reflect(bank_id, entity_name, query)` | What is known about one person or project, with the ids it cites. |
| `memory_forget(bank_id, text or payload_id)` | Only after the user confirms the exact payload you showed them. |
