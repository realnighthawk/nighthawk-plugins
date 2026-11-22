# Chips

Chips are season data, not memory. Read them from the downloaded bootstrap data every time (`boot.json` -> `chips`:
each has `start_event` and `stop_event`) and check the official announcement before asserting a rule; the chip list and
the split have changed between seasons.

## The shape to expect (verify, do not assume)

- Recent seasons split the chips into two sets, one per half of the season. A set expires at its last gameweek's
  deadline and does not carry over; the next set opens after it. `boot.json` gives each chip's `start_event` and
  `stop_event` - those two numbers are the truth for this season.
- One chip per gameweek.
- Anything that depends on a double or blank gameweek later in the season applies to the set that is open then, not to
  chips left over from the first set.

## Planning the open set

1. List what is left from the user's Chips tab (not from memory), and cross-check the current set's events in `boot.json`.
2. Run `model`: it prints the scheduled double/blank gameweeks it can see (unscheduled fixtures are not counted). If none
   fall before the set ends, Triple Captain and Bench Boost are single-gameweek plays.
3. Triple Captain: the best single gameweek for a premium player with a clearly easy home fixture; value ≈ one extra
   score of that player (≈ his points per game). Prefer a double gameweek if one exists.
4. Bench Boost: needs a bench that plays; value ≈ combined expected points of the four bench players (use the weekly
   table). Bank free transfers beforehand (up to the season's maximum) to upgrade the bench, then play it.
5. Free Hit: use-it-or-lose-it by the set's last gameweek; best in a blank gameweek or when injuries/fixtures wreck the
   squad.
6. Wildcard: after a wildcard has been played this set, the other chips in the set remain; the next set brings a fresh
   wildcard.
7. Compare with rivals' chips (`league` prints the chip played last gameweek; use the league_analyzer tool for chips
   remaining): a chip a rival has already spent in this set cannot be used again until the set resets, which is a small
   edge only until then.

Quote any estimated chip value as rough (season-average points per game), not a forecast.

## After a wildcard

Free transfers: 1 for the next gameweek, banked up to 5 if unused. Confirm the user's real number in the app. Not
transferring for a few weeks builds banked transfers that can upgrade a bench before a Bench Boost.
