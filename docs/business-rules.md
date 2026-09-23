# Business rules and data contract

All records are synthetic. Authoritative implementation: `service/engine.py`; orchestration and state: `service/store.py`.

## Input contracts

The CSV header contracts are in `SCHEMAS` in the engine. Every listed field must be nonempty; IDs must be unique within each table and contain only 1–64 ASCII letters, digits, underscores or hyphens. UTF-8 with an optional BOM is supported; surrounding field whitespace is stripped. Statuses and severity values must exactly match the documented lowercase enums. Dates must be real ISO `YYYY-MM-DD` dates. Source rows reference an existing project. Every project needs at least one task, exactly one budget, and at least one PM and one PMO stakeholder. Risk, milestone and dependency lists may legitimately be empty. A completely empty portfolio creates no project records or notifications.

| File | Identifier and key fields |
|---|---|
| projects | project_id, project_name, project_manager, currency |
| tasks | task_id, project_id, title, owner, due_date, status: open/in_progress/done |
| risks | risk_id, project_id, title, owner, severity: low/medium/high/critical; status: open/mitigating/closed; impact, action |
| milestones | milestone_id, project_id, title, baseline_date, forecast_date, status: open/done |
| dependencies | dependency_id, project_id, title, owner, critical: true/false; status: ready/blocked/resolved; impact, action |
| budgets | project_id, baseline, forecast, actual (finite nonnegative amounts; baseline > 0; forecast ≥ actual) |
| stakeholders | stakeholder_id, project_id, role: pm/pmo; name, email |

A malformed or missing file aborts the entire batch before snapshots are written. No missing budget, task list or unknown status is treated as healthy. Changes to all CSVs should be made while monitor scheduling is stopped; multi-file live ingestion does not have an atomic source-version protocol.

## Definitions

- Overdue task: not `done`, with due date strictly earlier than the as-of date. Work due today is not overdue.
- Overdue percentage: overdue tasks / all tasks × 100. Completed tasks remain in the denominator.
- Progress: completed tasks / all tasks × 100. This is unweighted task completion, not earned value or effort-weighted progress.
- Open milestone variance: `max(0, max(forecast_date, as_of_date) − baseline_date)`. The as-of floor detects an overdue open milestone even when its forecast was never updated. Completed milestones are excluded because actual completion dates are not captured.
- Overdue milestone: open milestone with baseline strictly earlier than the as-of date. Forecast slippage may exist before a milestone is overdue.
- High risks: unresolved `high` **plus** `critical` risks; `mitigating` remains unresolved.
- Blocked dependencies: every dependency with status `blocked`. Critical dependency is a separate boolean; graph cycle detection is not implemented.
- Forecast budget variance: `(forecast_at_completion − approved_baseline) / approved_baseline × 100`. Actual spend is displayed but is not the variance numerator. No earned-value index is inferred.
- Accomplishments: completed work **to date**, not claims of work completed this week.

## Scoring and thresholds

Start at 100. Subtract capped penalties: tasks up to 30 (`0.6 × overdue percent`), milestones up to 20 (`2 × maximum open slip days`), risks up to 20 (`8 × high + 15 × critical`), dependencies up to 15 (`5 × noncritical blocked + 15 × critical blocked`), budget up to 15 (`0.75 × positive forecast overrun percent`). Task and budget penalties are rounded to two decimals. The total is rounded to an integer using Python's round-to-nearest, ties-to-even behavior; minimum zero.

Cap at 59 for any unresolved critical risk, blocked critical dependency, budget overrun **>20%**, or open milestone variance **>10 days**. Otherwise cap at 79 for any unresolved high risk, budget overrun **>10%**, or variance **>5 days**. Exact threshold equality does not cross a strict `>` rule. Apply Healthy ≥80, At Risk ≥60, otherwise Critical.

These are transparent portfolio rules, not statistically validated forecasts. Threshold edits require engine, tests and documentation changes together.

## Escalation decisions

| Trigger | Level | Required action |
|---|---|---|
| Critical overall status | L2-PMO | Agree recovery plan and owners |
| Milestone >5 days late | L1-PM; L2 if >10 | Recover schedule or request baseline change |
| Unresolved high/critical risk | L1/L2 respectively | Source risk response |
| Blocked critical dependency | L2 | Source unblock action |
| Forecast budget overrun >10% | L1; L2 if >20% | Cost containment or funding decision |

A project can have several distinct issues plus an overall critical-health issue. Every escalation includes project, issue, severity, owner, impact, required action, due date, level and UTC processing timestamp. The due date is one calendar day after the snapshot for L2, two days for L1. This is a demo response SLA, not a business-day calendar or historical source due date.

## Idempotency and reporting cadence

- Daily snapshot key: `(snapshot_date, project_id)`. A batch checksum rejects changed input on the same date. Batches must arrive in increasing date order. The date is a Berlin business date; processing timestamps are UTC.
- A repeat of an identical daily batch is a no-op. Multiple intraday revisions are intentionally unsupported.
- Issue key: `project_id:issue_type_or_source_id`. An active issue of unchanged severity gets no new escalation each day. Resolution closes the episode; recurrence or severity change creates another episode. Impact/action wording changes alone do not create a new escalation.
- One report and one eligible notification per project-day. Daily status reminders are intentional; retry duplicates are suppressed. New escalation records for that snapshot are appended to the report's notification body.
- Healthy projects produce history and a report, without an outbox item. At Risk routes to PM, Critical to PM and simulated PMO.
- Frozen two-day demo initially queues historical and current status notifications. This is demonstration behavior; a real onboarding/backfill would need a suppress-historical-notifications option, which is not implemented.
- Notification leases are ten minutes. Each workflow invocation claims one item. Provider failure delays retry exponentially (60, 120, 240, 480 seconds); the fifth failed or expired final attempt becomes `dead`. A run that stops before acknowledging is recovered after lease expiry.
- Delivery is at least once across external systems. A provider acceptance followed by acknowledgement loss can duplicate a real message. Inspect the provider before retrying dead letters. No automatic dead-letter replay endpoint is exposed.
- Digest key: ISO week of the latest snapshot. A repeat refreshes that one week's record. It displays the source as-of date; it does not pretend an old frozen snapshot is current.
- Analytics is a full atomic CSV replacement, not append-only duplication. Raw immutable snapshot history remains in SQLite.

## Reporting safeguard

Every report section is built from validated fields or explicitly labeled rule-derived actions. Optional Ollama receives a fact map and can return only an exact permutation of its IDs. Extra, omitted, duplicated, mistyped or invented IDs fail validation. The service renders original fact text; model prose is never used. Timeout, transport failure or invalid output produces the complete deterministic report. This is intentionally constrained AI assistance, not free-form generative analysis or automated decision approval.
