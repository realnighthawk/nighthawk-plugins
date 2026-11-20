---
name: browser
description: Drives the person's real browser: reads or acts on a website they can see, signs in once through the live screen, and keeps the login in a profile. Use when a request needs a browser, a logged-in site, a login wall, a CAPTCHA or a human takeover, and as the next best option when a connected MCP tool is missing, blocked, fails or is weaker than the site itself. Not for engine-owned writes or approvals.
---

# The browser

The `auto_browser` connection is one real browser that keeps the person's logins. A session is disposable: its cookies
live only as long as the session. A login survives closing the session, or the pod restarting, only if it was saved as a
**profile**, and a later session only starts signed in if it is created from that profile. Nothing does either by itself.
Most "it logged me out again" comes from skipping the save.

This is also the fallback when a connected tool is missing, blocked or weaker than the site itself.

Call the `auto_browser:browser.*` tools directly, using the names and schemas the server advertises. If no
`auto_browser` tool is available, say the browser connection is not on (Connections, Signed-in Browser) and stop. Do not
fall back to another tool.

## If a tool is missing or a call fails

Before you tell the person a capability is missing:

1. Look for a connected tool that does the job.
2. If none covers it, or the tool call fails, and the result is visible on a website the person can see, use this browser
   flow.
3. Only then report what is missing.

This covers an API that is absent or blocked, a tool that returns an error, a page only a signed-in person can see, a
JavaScript-only UI, a transcript or article behind a login, or a feature the MCP surface does not expose. Use the
`auto_browser` MCP server; do not substitute a host browser or a browser prelude. It is not a way around an approval, a
credential rule, the host allowlist, or an engine that owns a record: a write the engine owns stays with the engine.
Reading, searching and summarising a page are normal; sending, posting, connecting, buying or changing an account
setting still needs the person to ask for that exact action.

## Rules that do not bend

- **Never ask for, read or type a password, a verification code or a recovery answer.** The person types them on the live
  screen. Do not use `auto_browser:browser.eval_js` or any tool to read cookies, tokens or storage.
- **Read-only unless asked.** Reading, searching, summarising and scrolling are the default. Sending a message, replying,
  connecting, following, posting, reacting, applying, buying and changing an account setting each need the person to ask
  for that exact thing in this conversation. Say what you are about to do and wait; one yes covers one action.
- **A session is yours only if you created it in this conversation.** Other agents and other chats use the same browser, and
  several sessions can be open at once on one shared screen. Give every session you create a `name` that starts with your own
  name and says the task, so the person can tell them apart. Never navigate in, take over, save a profile from, or close a session
  you did not create, even one on the site you want: it belongs to someone else's task. The session ids you hold are the only
  ones you act on.
- **One person's login per profile, one profile per site.** Name it for the site: `linkedin`, `google`, `tiktok`. Never
  put two accounts in one profile.
- **A challenge is a stop, not an obstacle.** A CAPTCHA, "unusual activity", a phone or app verification, or a restriction
  notice goes to the person (step 3). Do not retry in a loop and do not try to get around it: automated sign-ins can get an
  account restricted.

## 1. Find out what is already there

Call `auto_browser:browser.list_auth_profiles`, then `auto_browser:browser.list_sessions`. The site is in the request; the
sign-in and landing pages for the common ones are in [references/sites.md](references/sites.md).

- A profile for the site exists: go to step 2.
- No profile: go to step 3.
- A session you created earlier in this conversation is still open on the site: reuse it (observe it, then continue at
  step 4) rather than starting another.
- A session you did not create is open: leave it alone, and do not open a second one on a site another session is already
  signed in to, since two live sessions on one account can look like a takeover to the site. Tell the person what is open
  (`auto_browser:browser.list_sessions` shows the names) and ask whether to wait or whether they want it closed.
- If `auto_browser:browser.create_session` is refused for the session limit, the open sessions are other work. Say which ones, and
  ask. Never close one that is not yours to make room.

## 2. Start from the saved login

`auto_browser:browser.create_session` with `auth_profile` set to the profile name and `start_url` a page of the site that needs the
login (for LinkedIn, the messaging page), and a `name` that says the task. Then `auto_browser:browser.observe`.

- Signed in (the page shows the person's own content, not a sign-in form): go to step 4.
- A sign-in page, "session expired", or the create call is refused as stale or missing: the saved login no longer works.
  Close that session and go to step 3. Say so plainly ("your LinkedIn login has expired") rather than silently retrying.

## 3. Sign in once, with the person

1. `auto_browser:browser.create_session` with no profile, `start_url` the site's sign-in page, and a `name` that says the task.
2. `auto_browser:browser.request_human_takeover` for that session, with a `reason` the person will recognise ("sign in to LinkedIn").
   Give the person the link it returns, and say in one line what to do: open it, sign in (including any code), then tell you.
3. Wait for the person to say they are done. Do not poll, do not type, do not click the sign-in form yourself.
4. `auto_browser:browser.observe` to confirm they are in: their own page, not the sign-in form. If it is still a challenge page, ask
   them to finish it, once more; if it still is not in, stop and say what the page shows.

## 4. Save it before anything else

As soon as you have confirmed a signed-in page, call `auto_browser:browser.save_auth_profile` with `session_id` and `profile_name` (the
site's name from step 1), **before doing the task and before any close**. Then call `auto_browser:browser.list_auth_profiles` and check
the name is there. If the save fails or the profile is not listed, tell the person it did not save and that closing the
session will sign them out; do not carry on as if it worked.

A session that was started from a saved profile and is still signed in should be saved again at the end (step 5): that
keeps the profile fresh. The controller refuses a profile past its age limit (30 days in the current setup): sign in
again and re-save rather than treating the refusal as a broken login.

## 5. Do the task, then finish cleanly

Do what was asked with `auto_browser:browser.execute_action` (navigate, scroll, click), `auto_browser:browser.observe`, and the reading tools
(`auto_browser:browser.get_html`, `auto_browser:browser.find_elements`, `auto_browser:browser.screenshot`). Prefer reading the page text to clicking around; go
page by page and slowly, as a person would.

If a navigation is refused with "not allowlisted", the browser may only visit the hosts it is configured for. Tell the
person which host it was and stop: adding one is a deployment setting, not something to route around.

If a call returns `approval_required`, the person must approve it on the browser's own dashboard. Say so and wait; do not
repeat the call.

Finish: if the session you created was signed in and used, call `auto_browser:browser.save_auth_profile` again, then
`auto_browser:browser.close_session` on it, and only on it. If the person asks you to close the session and a login was made in it
that is not saved, save it first, or tell them that closing will sign them out and ask. Report what you did and what you
saw, in the person's terms; never include a cookie, token or page source in the answer.

## When something goes wrong

Say what happened and what the page showed. A session of yours that behaves oddly (a blank screen, a stuck page) is closed
with `auto_browser:browser.close_session` and recreated once; a second failure goes to the person. Do not keep a session open "just in
case": it takes a place another agent may need.
