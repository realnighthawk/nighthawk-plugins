---
name: manage-goals
description: Sets up and manages the person's goals, habits, tasks, reminders and events: starting a goal such as "run a 10K by March", "lose 5 kg", "learn Spanish", "save for a deposit" or "organise the move" together with the tasks and events that serve it, or adding a single task, reminder or calendar event; editing, moving, snoozing, completing, archiving, restoring or undoing what exists; recording a measurement or progress. Use when the person says something they want to achieve, a project or habit to start, or asks to change, complete or measure something already set up.
---

# Managing goals

Everything here is the person's own record: it can be edited and undone, so make the change and tell them what you did.

Call the `life` server's tools directly, using the names and schemas it advertises. If no Life tools are connected, say
goal tracking is not connected and create nothing. The browser is not a substitute for the engine's writes.

## When the engine is the right place

The Life engine is the person's own system of record: goals, tasks, events, recurring items, watches, reminders and the
artifacts that show them. When a request involves something to track, repeat, schedule or watch, use the engine. A passing
remark needs nothing recorded. A result the person will want to look at again (a plan, a report, a tracker) can be shown as
an artifact: use the `view-builder` skill when it is available; skip it when an artifact would add nothing.

### Work of your own, later or on a repeat

When the person wants something done again or at a time and you must do it ("send me recommendations every week"), set
a reminder for yourself: an item with `subject: "agent"`, a time, usually a repeat, and an alert. Their screens do not
show it. When it comes due it reaches you as a message from yourself, in the conversation you created it from, and it is
a request like any other: the skill it matches runs. You will have nothing else in front of you then, so the text is all
of it:

- Write the job itself, as they would ask for it: "Plan this gameweek for FPL team 2452109 and put the recommendations in
  the goal 'Weekly FPL'". It has to match the skill that does the work, so name that work plainly and do not lead with
  words that belong to another skill (goal, view, set up).
- Make it stand alone: every id, name and choice from this conversation. Say where the result goes. One job per reminder.
- Create it from the conversation they will see the results in. If they gave no time, pick one and say so. The engine
  refuses repeat shapes it cannot do; read its answer. Read the item back to confirm its time zone and repeat, then tell
  them what will happen in their terms ("I'll plan each gameweek on Tuesdays at 09:00 and post it to your goal").

When one comes due, do what it says as you would for the person's request. If the same job is still running from last
time, say so. When the work finishes, do what the reminder said with the result, and tell them what you did.

## The model, in the person's words

- A **goal** is an outcome, which the engine stores as an *intention* and whose tools are named `intentions_*` ("run a 10K
  by March", "the kitchen renovation, June 3-10"). Give it an end date if it finishes; leave it open if it does not.
- A **task** waits for someone to do it. A time on it is a deadline or a cue ("call Sam at 5"), not an appointment.
- An **event** happens at a time whether or not anyone acts, and the person shows up (a flight, a dinner, a meeting).
- A **reminder** is not a thing of its own: it is a task or event with an alert (`alert_before_minutes`; 0 means at the time).
- A **routine or habit** is a task that repeats (`recurrence`). Give it an alert if they want to be told.
- A task or event serves a goal through a `serves` link (`life:links_set`). Never copy one into the goal.

## 1. Which mode?

- **A goal** is an outcome with parts or a time frame: "run a 10K by March", "organise the move", "host a dinner". Create
  the goal and the tasks and events that serve it.
- **A single task or event** is not a goal: "remind me to call Sam at 5" is a task with an alert; a lone meeting is an
  event. Create or change it directly, without a goal.
- **A change** is anything already set up: edit, move, snooze, complete, archive, restore, delete or undo it.
- A trip or travel plan is `travel-planner`. A spending limit is a budget, not this. A passing wish is not one yet:
  answer them and offer.

## 2. See what exists

Call `life:intentions_list` and `life:tasks_list` together (add `subject: "agent"` when it could be a reminder or goal
you set for yourself). If a goal they already have looks like this one, ask whether to change that goal (name it) or
create a new one, and wait for the answer. If a task they already have serves the new goal, link it with `life:links_set`
after the setup (the task `serves` the goal, which the engine stores as an intention); a link is a change, not a
creation.

## 3. Create a goal

### 3a. Have enough

You need the outcome, the time frame if it has one (an end date or the dates that matter), and for a trip or event the
dates and place. Ask for what is missing, one thing at a time, and only what would change what you build. Never invent a
fact. Write what you have to `brief.md`: the outcome, the time frame, dates and place, and anything the person said that
shapes the plan.

### 3b. Build the plan

Write the plan as JSON to `plan.json`:

```json
{
  "goal":   {"title": "...", "notes": "...", "ends_on": "YYYY-MM-DD"},
  "tasks":  [{"title": "...", "notes": "...", "at": "YYYY-MM-DDTHH:MM", "minutes": 20,
              "alert_before_minutes": 0, "is_priority": false,
              "recurrence": {"freq": "daily|weekly|monthly", "interval": 1, "weekdays": [1, 3]}}],
  "events": [{"title": "...", "notes": "...", "at": "YYYY-MM-DDTHH:MM", "minutes": 90, "alert_before_minutes": 60}]
}
```

Everything except `goal.title` and at least one task or event is optional. `weekdays` are 0 (Sunday) to 6, weekly only.
Do not write ids, links or time zones: the script adds them. A plan holds at most 24 tasks and events together.

Design it:

- **Goal.** `title` is the outcome in their words; `notes` holds short reminders for the whole thing; `ends_on` if it
  finishes.
- **Tasks.** Small and concrete, so there is always a next action. Give each an `at` (deadline or cue) when one matters.
  Time it relative to the end date the way a sensible person would: for a move, book the van weeks ahead, confirm the
  keys the day before, pack the day before. Use `minutes` for how long it takes.
- **Events.** Things fixed in time: flights, hotel check-in, the dinner itself. Give each `at`, `minutes`, and an alert
  only where being told ahead helps.
- **Repeats.** A habit that serves the goal is a task with `recurrence` (daily, weekly on chosen weekdays, or monthly).
  Keep its alert on the same day as its time.
- **Your own follow-ups.** A reminder for yourself is a task with `subject: "agent"`, an `at`, `alert_before_minutes: 0`,
  and the job itself in the title and notes. It wakes this conversation.
- **Times** are the person's local wall-clock time, `YYYY-MM-DDTHH:MM`, always with an hour and no zone. If they give a
  vague time ("tomorrow", "in the morning") with no hour, ask for the hour rather than guessing.

### 3c. Check and apply

1. Read the person's zone with `life:settings_get` → `time_zone`.
2. Run `python3 scripts/goalplan.py check plan.json --tz <zone>`. Fix every problem it prints and run it again. It
   prints `{"ok": true, "problems": []}` when the plan is fit to try.
3. Run `python3 scripts/goalplan.py build plan.json --tz <zone>`. It prints `goal_id`, `idempotency_key`, `operations`
   and a `summary` of what will be created.
4. Call `life:batch_dry_run` with the `operations`. Fix any refusal and build again.
5. Call `life:batch_apply` with the printed `idempotency_key` and `operations`.

The batch is all or nothing. Do not report the setup as made until the apply succeeds. Keep that idempotency key as the
undo key.

## 4. Create a single task or event

Use `life:tasks_create` for something to do: a time is a deadline or a cue, `alert_before_minutes` makes it a reminder,
and `recurrence` makes it a habit. Use `life:calendar_events_create` for something that happens at a time whether or not
anyone acts (a meeting, a flight, a dinner), with `at`, `minutes` and an alert where it helps. Link it to a goal with
`life:links_set` (`from_kind` task or event, relation `serves`, `to_kind` intention) when it serves one; otherwise leave
it unlinked. Every direct create or link call takes a fresh `idempotency_key`. Do not create a goal for a single item.

## 5. Change what exists

Edit, do not start over. Every direct write takes a fresh `idempotency_key`; an edit, completion, snooze or archive also
needs the version you last read (`expected_version`). An update replaces the record's fields, so read the record first
(from `life:intentions_list`/`life:tasks_list`, or the matching `*_get`), then send every field you want kept, including
`title`, along with the change: `life:intentions_update`, `life:tasks_update`, `life:calendar_events_update`.

Use the tool that matches what they said: `life:tasks_complete` for done (a repeating task completes one occurrence: name
it with `at`; an agent task takes `result`), `life:tasks_snooze`/`life:calendar_events_snooze` to defer an alert without
moving the item, `life:intentions_archive`/`life:intentions_restore` to put a goal away or bring it back, and the
delete/restore tools when they want something gone (it can be restored). When a date moves (a flight, a deadline), look
at what depends on it with `life:links_list` for the goal (`kind` intention) and move those too, telling the person what
you changed; ask first if it is not obvious.

If the request is ambiguous ("clear them all" after a list), ask which records they mean before changing anything.
Archive is reversible; delete is restorable; still say what you are about to change.

To take back a whole setup, call `life:batch_undo` with a fresh `idempotency_key` and `batch_key` set to the undo key
from the report that set it up.

## 6. Progress

When they tell you a measurement ("I'm 81.5 today"), record what they said with `life:activities_record` (a fresh
`idempotency_key`, `kind: "measurement"`, `text` in their words, `occurred_at` now) and tie it to the goal with
`life:links_set` (`from_kind: "activity"`, `relation: "evidences"`, `to_kind: "intention"`). If a tracker artifact's app
takes logged values, `view-builder` says how to use it. Only record what they said.

## 7. Tell the person

Once the setup or change is applied, write your report in plain words: the goal (if any), the first few tasks and events
with their times, which ones will tell them ahead of time, what changed and why, and that they can ask for any change.
Include the undo key on its own line as `Undo key: <key>`. Do not invent anything.
