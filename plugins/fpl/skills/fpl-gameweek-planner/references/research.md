# Research playbook (the internet = hypotheses layer)

Goal: a list of **claims to test**, not decisions. Spend a few searches, not a rabbit hole. Contents: sources, queries, what to extract, output format, caveats.

## Sources and how to reach them

| Source | Tool | Notes |
|---|---|---|
| Articles: Fantasy Football Hub, FFScout, OneFPL, FPL Copilot, All About FPL, Never Manage Alone, fpltilt, premierfantasytools (press-conference summaries) | `exa` `web_search_exa`, then `web_fetch_exa` on the best URLs (or another search/fetch tool your client provides) | Some sites return 403. Ask the fetch tool for tables/lists, not summaries. |
| r/FantasyPL | the `reddit` server's `browse_subreddit` (hot) (use the tool your client exposes) | Without Reddit API credentials it uses the RSS feed: titles/bodies only; scores, comment counts, `search_reddit` and `get_post_details` fail. Web fetch/search tools are often blocked for reddit.com; if so, use the `reddit` server rather than retrying. |
| Podcasts / YouTube | `exa` `web_search_exa` for titles; a connected YouTube/transcript tool, or the built-in browser on the video's transcript page | If neither reaches the transcript, only titles/descriptions are reachable. Say so; ask the user to paste one if audio content matters. |
| Official: premierleague.com news (chip rules, deadlines) | `exa` `web_search_exa`/`web_fetch_exa` | Use for rules, not opinions. |

## Queries (adapt names and gameweek)

- `FPL Gameweek <N> captain picks <season>`
- `FPL GW<N> wildcard draft <season>` / `best wildcard team gameweek <N>`
- `FPL GW<N> transfer tips buy sell hold`
- `FPL GW<N> injury news press conference summaries`
- `FPL chip strategy guide <season> first set` (rules + timing ideas)
- Specific to the user's squad: the names of their players plus "injury" or "price rise".

## What to extract

Captain consensus and the differential captain; injuries and return dates; buy/sell/hold lists with reasons; wildcard drafts (the 15 players, prices, formation) and what the common core is; chip timing; price-change predictions; fixture swings; names the user asked about specifically. Record the source and date for each.

## Output: the claims table (save as `research.md`)

| Claim | Source(s) | Direction | Status |
|---|---|---|---|
| Haaland best captain GW8 | Yahoo, Rotowire, ... | captain | to test |
| Saka out 6+ weeks | Reddit headline, Arteta quote | sell | to test (injury status in data?) |

Leave Status as "to test"; the statistics step fills it. Note conflicts between sources (e.g. one site assumes a player is doubtful, another says fit) and mark facts that need a primary check (injury status is in the downloaded data's `status`/`news`).

## Caveats to state

- Articles often recommend what is already popular; the numbers decide.
- Prices differ by site and time (±£0.1m); use the data.
- Anything dated before the latest deadline may be stale. Record each claim's date and check it against the downloaded
  data before repeating it.
