---
description: Save a fact, decision, or preference to long-term memory
argument-hint: <what to remember>
---

Save this to long-term memory: $ARGUMENTS

Bank: !`printenv NIGHTHAWK_BANK || printenv AGENT_BRAIN_BANK || echo agent-harness`

Protocol:

1. `memory_recall` with the bank and the people, projects, or topics in the
   fact. If memory already holds it, say so; retain again only if this version
   corrects or extends it.
2. `memory_retain` with the same bank and `text` as one short, plain-sentence
   account of what happened or was decided — from the user's side, with the
   date when it matters ("On 2026-10-27 the user decided ..."). Retain what the
   user said or decided, never the recalled block itself.
3. Report what was saved in one line. If the call fails, report the error —
   do not claim it was saved.
