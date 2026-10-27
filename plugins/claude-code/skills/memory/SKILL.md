---
name: memory
description: Use agent-brain long-term memory deliberately. Use when the user asks to remember, recall, forget, or look up something about a person, project, or earlier decision, or asks what you know about them.
---

# Agent-brain memory

The plugin already recalls relevant facts before each prompt (the block tagged `<agent-brain-memory>`) and
writes finished parts of the session back. Use the tools below only when the user asks for something the
automatic path does not cover. Every call takes the same `bank_id`, the value of `AGENT_BRAIN_BANK`.

| Tool | Use it when |
|---|---|
| `memory_retain(bank_id, text, mention_time?)` | The user says "remember this". `text` is a short account of events between named people or things, in plain sentences. |
| `memory_recall(bank_id, query)` | You need facts the injected block lacks. Fast; reads only. |
| `memory_reflect(bank_id, entity_name, query)` | The user asks what is known about one entity, such as a person or project. Returns an answer with the ids it cited. |
| `memory_build_entity_profile(bank_id, entity_name)` and `memory_build_entity_relations(bank_id, entity_name)` | The user wants an entity's type, attributes, or relations rebuilt now. |
| `memory_forget(bank_id, text)` | The user asks to forget something. Pass the exact text of the payload to remove, or its `payload_id`. It removes the payload, the facts only it supported, and everything derived from them. Confirm with the user before calling it. |

Rules:
- Never retain recalled memory back as new text. Retain what the user said or decided in this session.
- Do not claim memory holds something unless a recall or reflect result in this conversation shows it.
- A fact the user corrects should be retained as the correction, with the date, so the newer fact is the one recalled.
