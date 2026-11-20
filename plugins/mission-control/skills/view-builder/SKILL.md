---
name: view-builder
description: Builds or updates a view for a goal, task or event, and surfaces a result with it: composes the manifest from the view kit, wires live blocks to the Life APIs, puts static values in the manifest, and creates or updates the view. Use whenever a goal, task or event is created, a result is produced that the person will want to see again, or the person asks to build or update a view, surface a result, or make a dashboard. Not for rendering arbitrary files, markdown, images or tables; the view kit cannot draw those.
---

# Building a view

A view is a client-rendered manifest for a goal, task or event (a goal is an *intention* in the engine: `subject_kind` is
`intention`, `task` or `event`). Build or update one when you create a goal, task or event, or when a result is worth
seeing again (a plan, report, booking, analysis — not a scratch file). Skip it when a view would add nothing, and say why.

Call the `life` server's tools directly, using the names and schemas it advertises. If no Life tools are connected, say
so and create nothing.

## Strictly the kit

Call `life:tracker_catalog_get` (no arguments) before composing; use its exact `catalog_id` and only its blocks, functions and
formats. Never invent a block or markup. The client renders the manifest; you do not render it.

## Wire the data

- **The subject's own records.** Use the `tasks` and `events` blocks; the client reads the Life APIs for that goal, task or
  event. Goal progress is the `tasks` block, not a metric.
- **A repeating task's history.** A metric with `task_id`; the values are its done occurrences, one per day.
- **A connected provider.** A metric with `source` (provider + series); read that provider's catalog first.
- **Static data in the manifest.** `const`/`date` in a calculation for one value, a target or a threshold; `text` for words
  (no figures, up to five short points); `link` for an artifact (absolute http/https only). The kit has no literal series or
  table: for those, record measurements or use a provider; otherwise a `text` summary + `link` is the honest surface.
- **Numbers a person logs.** `life:measurements_record` with a fresh `idempotency_key`, `subject_kind`, `subject_id`,
  `metric_id` and the `value`; the metric has neither `source` nor `task_id`.
- **Never invent a figure.** Put numbers in metrics and calculations, not in prose.

## Compose

Lead with a hero `sentence` whose numbers come from calculations. Choose blocks by the shape of the data: `bar` for a
scale, `series` for change over time, `grid` for days, `steps` for thresholds, `timeline` for dates, `tasks`/`events` for
the subject's records, `log` for a value the person records, `text` for static words, `link` for an artifact. Organise
pages of titled sections; one page unless the subject has genuinely separate concerns.

Limits: 0-6 metrics, 1-4 pages, 1-6 sections, 1-8 blocks each (16 in all), a calculation nests five levels, a sentence has
at most six slots.

## Attach it

A view needs a goal, task or event. If a result has no subject, create a person-visible task (or goal) as its container;
never invent a free view. One live view per subject per catalog: read `life:views_state` (or `life:views_list` for every
catalog) first; if a view exists, `life:views_update` with `expected_version` and keep every metric that has recorded
values, in the same unit; otherwise `life:views_create`. Both take a fresh `idempotency_key`. Read `life:views_state`
back, then tell the person
where to see it. Complete the container; do not delete or archive it.
