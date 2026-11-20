# Sites the browser is set up for

The browser may only visit the hosts it is configured for (the tenant chart's `autoBrowser.allowedHosts` and `googleDomains`).
A site that is not on that list is refused at navigation; the fix is a deployment setting, not a workaround.

| Site | Profile name | Sign-in page | Where the work usually is | Signed in when |
|---|---|---|---|---|
| LinkedIn | `linkedin` | `https://www.linkedin.com/login` | `https://www.linkedin.com/messaging/`, the person's own profile, `/feed/` | the page shows the person's name or inbox, not "Sign in" |
| Google | `google` | `https://accounts.google.com/` | `https://myaccount.google.com/`, `https://mail.google.com/` | the account page or inbox loads, not a sign-in form |
| TikTok | `tiktok` | `https://www.tiktok.com/login` | | the person's avatar and "Upload" show |

TikTok is listed so the profile name is settled. Check whether its host is allowlisted before promising it; if navigation
is refused, say so rather than routing around the allowlist.

## LinkedIn

- Sign-in sometimes asks for an emailed code or a phone prompt. That is the person's to complete on the live screen.
- LinkedIn is strict about automation. It may show a verification step after a login from a server, or restrict an account that
  behaves like a script. Read slowly, one page at a time, and stop at the first sign of a restriction notice.
- Messages load as a list on the left and the open thread on the right. Read the thread you were asked about; do not open every
  conversation "to be thorough".
- Reading a thread can mark it as read. Say so before opening one if it matters to the person.

## Google

- Sign-in passes through several Google hosts and may land on the country site for the person's location
  (`accounts.google.co.in`); all of Google's own country sites are allowed.
- A signed-in Google profile also signs the person in to YouTube and other Google sites. Treat it as the whole account.
