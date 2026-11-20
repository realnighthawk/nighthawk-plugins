---
description: Use the deployed auto_browser MCP for browser work, and as the fallback when a tool is missing or a call fails.
alwaysApply: true
---

# Browser work goes through auto_browser

For any browser work in this plugin — opening a site, reading a logged-in page, or doing what an MCP tool cannot — use the
`browser` skill and the `auto_browser` MCP server (`auto_browser:browser.*`). That is the deployed, shared browser that
holds the saved profiles. Do not use oh-my-pi's built-in `browser` Eval prelude for tenant work.

If a connected tool is missing, blocked, or a tool call fails, attempt the browser flow before reporting the capability
missing. The browser cannot replace a write the Life/TREK/engine owns, and it cannot approve for the person.
