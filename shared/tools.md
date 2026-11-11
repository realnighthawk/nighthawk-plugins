| Tool | Use it when |
|---|---|
| `memory_recall(query)` | You need facts from earlier sessions. Reads only. |
| `memory_retain(text, mention_time?)` | The user says "remember this", or states a decision, preference or correction. One short dated plain-sentence account. |
| `memory_reflect(entity_name, query)` | What is known about one person or project, with the ids it cites. |
| `memory_forget(text or payload_id)` | Only after the user confirms the exact payload you showed them. |
