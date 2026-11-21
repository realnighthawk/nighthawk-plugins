---
name: view-builder
description: Builds or updates a Life Engine view for a goal, task or event. Use when the person wants a reusable result, plan, report, or dashboard. Compose native ViewKit blocks for live data and Markdown where the catalog and client support it. Not for rendering arbitrary files.
---

# Building a view

A view is a client-rendered manifest for a goal, task or event (a goal is an *intention* in the engine: `subject_kind` is
`intention`, `task` or `event`). Build or update one when you create a goal, task or event, or when a result is worth
seeing again (a plan, report, booking, analysis — not a scratch file). Skip it when a view would add nothing, and say why.

Call the `life` server's tools directly, using the names and schemas it advertises. If no Life tools are connected, say
so and create nothing.

For a standalone document or slide deck, use `life:artifacts_create` when available. Set `mode` to `document` or `deck`;
each ViewKit page is one slide in `deck` mode. Do not create a task just to hold an artifact. Read `life:artifacts_get`
before revising, send the full manifest with stable page, section and block IDs to `life:artifacts_update`, and use the
version last read as `expected_version`. Reuse the same idempotency key for a retry of the same write. In Mission Control
Apple chat, return `[artifact title](life-artifact://ARTIFACT_ID)`. On other clients, return the title and ID unless the
client supplies its own link format. For standalone artifacts intended for Apple chat, use Markdown, text and link blocks.

## Strictly the kit

Call `life:tracker_catalog_get` (no arguments) before composing; use its exact `catalog_id` and only its blocks, functions and
formats. Never invent a block. The client renders the manifest; do not generate HTML or scripts.

## Wire the data

- **The subject's own records.** Use the `tasks` and `events` blocks; the client reads the Life APIs for that goal, task or
  event. Goal progress is the `tasks` block, not a metric.
- **A repeating task's history.** A metric with `task_id`; the values are its done occurrences, one per day.
- **A connected provider.** A metric with `source` (provider + series); read that provider's catalog first.
- **Authored content.** Use `markdown` for prose, lists, code and static tables only when the catalog advertises it and the
  destination client supports it. Otherwise use `text` for a short summary and `link` for an existing artifact.
- **Live or derived numbers.** Bind to metrics and calculations. Use `const`/`date` for fixed targets and thresholds.
- **Numbers a person logs.** `life:measurements_record` with a fresh `idempotency_key`, `subject_kind`, `subject_id`,
  `metric_id` and the `value`; the metric has neither `source` nor `task_id`.
- **Never invent a figure.** Use Markdown tables for sourced or user-provided facts, not snapshots of live metrics.

## Compose

Lead with a hero `sentence` for a dashboard, or Markdown for a prose-first result. Use `bar` for a scale, `series` for change
over time, `grid` for days, `steps` for thresholds, `timeline` for dates, `tasks`/`events` for the subject's records, and
`log` for a value the person records. Organise pages of titled sections; one page unless the subject has separate concerns.

Limits: 0-6 metrics, 1-4 pages, 1-6 sections, 1-8 blocks each (16 in all), a calculation nests five levels, a sentence has
at most six slots.

## Attach it

A view needs a goal, task or event. If a result has no subject, create a person-visible task (or goal) as its container;
never invent a free view. One live view per subject per catalog: read `life:views_state` (or `life:views_list` for every
catalog) first; if a view exists, `life:views_update` with `expected_version` and keep every metric that has recorded
values, in the same unit; otherwise `life:views_create`. Both take a fresh `idempotency_key`. Read `life:views_state`
back, then tell the person
where to see it. Complete the container; do not delete or archive it.
