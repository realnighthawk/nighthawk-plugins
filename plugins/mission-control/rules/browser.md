---
description: Browser work uses oh-my-pi's built-in browser, which is attached to the person's workstation.
alwaysApply: true
---

# The browser is the built-in browser

For any browser work (opening a site, reading a logged-in page, doing what an MCP tool cannot) use oh-my-pi's built-in
`browser`. It is attached to the person's workstation, a computer of their own that has the open web and keeps their
saved logins, so it is already signed in where they signed in. There is no separate browser connection and none to ask for.

- If the built-in browser is not attached to a workstation, say so once and stop. Do not look for another browser tool. Tell the person to quit and start omp with `mc omp`, which attaches their workstation (or to create the workstation at `/workstation` in Mission Control if it does not exist). If `mc` is not installed, they install it with the one line shown on that page.
- Never ask for, read or type a password, verification code or recovery answer, and never read cookies, tokens or storage.
  When a sign-in, a CAPTCHA or a decision needs the person, say so and point them to the Workstation page in Mission
  Control (`/workstation`), where they can take over the same screen. Wait for them to say it is done.
- Read-only unless asked. Reading, searching, summarising and scrolling are normal. Sending, posting, replying,
  connecting, following, buying, applying and changing an account setting each need the person to ask for that exact action.
- If a connected tool is missing, blocked or fails, and the answer is on a site the person can see, the browser is the
  fallback before you report the capability missing. It cannot replace a write the Life, TREK or other engine owns, and it
  cannot approve anything for the person.
