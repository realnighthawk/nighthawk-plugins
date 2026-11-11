---
name: reactor
description: Use the Reactor hub to reach the user's connected services (maps, finance, trips, tasks, FPL, Notion and more). Use when a task needs a capability you have no direct tool for.
---

# Reactor hub

The `reactor` MCP server aggregates tools from many backends behind four tools:

- `search_tools(query, top_k)` finds a tool by what it does. Returns `server`, `tool` and `input_schema`.
- `call_tool(server, tool, arguments)` runs it, with `arguments` built from that `input_schema`.
- `search_skills(query, top_k)` and `get_skill(name)` return curated procedures for how to approach a task.

Before concluding you lack a tool, call `search_tools`. Never guess a server or tool name; backends change, so search again each turn rather than trusting what you remember. If nothing matches, say so. If `reactor` needs sign-in, say so once and continue.
