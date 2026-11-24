---
description: Browser work uses oh-my-pi's built-in browser, which is attached to the person's workstation.
alwaysApply: true
---

# The browser is the built-in browser

For any browser work (opening a site, reading a logged-in page, doing what an MCP tool cannot) use oh-my-pi's built-in
`browser`. It is attached to the person's workstation, a computer of their own that has the open web and keeps their
saved logins, so it is already signed in where they signed in. There is no separate browser connection and none to ask for.

- If the built-in browser cannot connect, say so once and stop. Do not look for another browser tool. The usual cause is that the workstation does not exist or is asleep: tell the person to create or wake it at https://mission-control.nighthawklabs.org/workstation. If you are running in the person's own terminal (not on the platform), they instead quit and start omp with `mc omp`, which attaches their workstation; if `mc` is not installed, the same page shows the one line that installs it.
- Never ask for, read or type a password, verification code or recovery answer, and never read cookies, tokens or storage.
  When a sign-in, a CAPTCHA or a decision needs the person, say so and point them to the Workstation page, https://mission-control.nighthawklabs.org/workstation, where they can take over the same screen. Always write that full address on its own, never the bare path, so it is a link in a terminal. Wait for them to say it is done.
- Clean up after yourself. The workstation is the person's own browser and they may be watching it. Keep a note of each tab you open, and close every one of them when you are done with it or when the task ends, including on an error or if you stop early. Never close a tab you did not open (the person's own tabs and windows are theirs), and leave the browser itself running. Reuse one tab for a sequence of pages rather than opening a new one each time.
- Read-only unless asked. Reading, searching, summarising and scrolling are normal. Sending, posting, replying,
  connecting, following, buying, applying and changing an account setting each need the person to ask for that exact action.
- If a connected tool is missing, blocked or fails, and the answer is on a site the person can see, the browser is the
  fallback before you report the capability missing. It cannot replace a write the Life, TREK or other engine owns, and it
  cannot approve anything for the person.
