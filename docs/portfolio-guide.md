# Portfolio and interview guide

Use these statements only within the validation boundary recorded in this repository. After completing your own n8n smoke tests, you may accurately add that you imported and ran the workflows locally. Do not claim an employer deployment, production usage, paid AI service integration, cost savings or reduced project delays.

## Suggested GitHub repository

Name: `n8n-project-delivery-automation`

Description: Local-first PMO automation with six n8n workflows, transparent project-health rules, durable escalation and notification state, optional Ollama reporting, and Power BI-ready synthetic history.

Topics: `n8n`, `workflow-automation`, `project-management`, `pmo`, `python`, `sqlite`, `docker-compose`, `risk-management`, `stakeholder-reporting`, `ollama`, `power-bi`, `portfolio-project`, `synthetic-data`.

## Three CV bullets

- Built a synthetic project-delivery automation portfolio with six n8n workflow exports and a Python/SQLite service covering 10 projects and 120 tasks, including health scoring, risk escalation and stakeholder report generation.
- Implemented transactional daily snapshots, recurring-issue tracking and a leased notification outbox, with automated tests for duplicate execution, concurrent claims, validation failures and recovery after interrupted processing.
- Produced Power BI-ready historical CSV data and deterministic project reports, with an optional local Ollama adapter restricted to verified fact ordering and a fallback for unavailable or invalid model responses.

These bullets quantify implemented scope, not business outcomes. Avoid “deployed enterprise-wide”, “automated real client reporting”, “eliminated all duplicates” and “AI predicted project failure”.

## LinkedIn project description

**Project Delivery Automation Hub | Personal portfolio project**

I built a local-first PMO automation project to explore how project updates can become consistent, traceable delivery information.

Six n8n workflow exports coordinate health monitoring, risk escalation, status reporting, stakeholder notifications, a weekly portfolio digest and historical analytics. A small Python/SQLite service handles the business rules and durable state.

The demonstration uses 10 synthetic projects and 120 tasks, including delayed milestones, blocked dependencies, budget overruns and a recovering project. Reports work without a paid AI service; optional Ollama assistance is limited to ordering verified facts.

I tested the business logic, duplicate protection and local HTTP pipeline. n8n import/execution and live integrations are separate local acceptance steps, documented alongside the test results.

All data is synthetic. This is independent portfolio work, with no employer deployment or measured business impact claimed.

#ProjectManagement #n8n #PMO #WorkflowAutomation

After actually completing the n8n smoke tests, update the validation paragraph with the version and date you tested; do not leave an inaccurate “untested” statement or claim an unperformed test.

## Interview questions and factual answers

**1. What problem does this solve?**
It makes task, milestone, risk, dependency and budget exceptions visible in a consistent project review. The demonstration shows the workflow and governance logic; it does not measure savings in a real organization.

**2. Why use n8n and a separate Python service?**
n8n provides visual schedules, routing and integration nodes. The service keeps validation, scoring and durable state in one testable module. SQLite transactions are more appropriate for this demo's deduplication than in-memory variables. The trade-off is an additional container and some coded logic rather than a pure low-code solution.

**3. How is health calculated?**
Five capped penalties reduce a 100-point score. Critical risks and dependencies, large forecast overruns and significant milestone slips cap it at Critical. That prevents one serious governance issue being hidden by other good metrics. The thresholds are explicit assumptions, not calibrated predictions.

**4. How do you distinguish risk from issue?**
A risk describes uncertain impact; an overdue task or blocked dependency is an observed condition. Unresolved high risks still justify escalation under the rules. The escalation table records the action and owner regardless of source type; it does not claim the uncertainty has already occurred.

**5. How do you prevent duplicates?**
Daily snapshots use project/date keys; escalations use issue episodes; reports and outbox items use snapshot keys. SQLite unique constraints and transactions enforce those decisions. A lease token controls one notification claim at a time, and acknowledged items cannot be reclaimed.

**6. Is external delivery exactly once?**
No. If a provider accepts a message before the acknowledgement is committed, a retry can send it again. The design is at least once at that boundary. Provider idempotency or reconciliation would be required for stronger guarantees.

**7. What happens when data is missing?**
The batch fails validation before any new project snapshot is written. Missing required values, malformed dates, orphan IDs, absent budgets and tasks are never interpreted as a healthy project. The n8n execution shows the failure and the source must be corrected.

**8. What happens if AI fails or hallucinates?**
The complete deterministic report is already available. Optional Ollama can only return an ordering of known fact IDs. The output must contain every ID exactly once; the service ignores model prose. Invalid responses or transport failures use the fallback. This is bounded assistance, not free-form analytical generation.

**9. Why forecast variance instead of actual spend variance?**
Actual spend can look low simply because a project is early. Forecast-at-completion versus the approved baseline indicates expected total overrun. The system displays actual spend but does not infer earned-value metrics without the necessary data.

**10. How are trends calculated?**
The current integer health score is compared with the previous saved snapshot for that project. The synthetic baseline is scored by the same engine. Positive change means Improving, negative means Deteriorating, zero Stable; a first snapshot is New.

**11. What did you actually test?**
The repository includes executed Python tests for scoring, malformed data, persistence, concurrency, failure recovery and the local HTTP pipeline, plus static checks of all six workflow exports. The evidence records the exact count and run timestamp. Docker/n8n/SMTP/Slack/Ollama runtime checks must be reported only after I perform them on my PC.

**12. What would change before real deployment?**
Authentication and TLS for the service; approved source connectors; retention and migrations; backups and restore tests; dead-letter operations; provider idempotency; load testing; access controls; and an approved governance model. Those are documented gaps, not features I claim to have implemented.

**13. What is the difference between stage scheduling and event processing?**
The scheduler wakes each workflow. Durable snapshots and queue records determine the actual work. The system polls these events; it does not use live external webhooks or a message broker. This is simple to demonstrate but adds polling latency.

**14. What happens to a resolved risk that returns?**
The next snapshot closes an issue episode when its condition is absent. If the same issue returns in a later snapshot, a new episode is created. A severity change also creates a new escalation; an unchanged active issue does not create a duplicate escalation each day.

## Limitations to disclose

Synthetic data only; no employer deployment or measured business effect. n8n runtime validation depends on the local installation. Companion-service architecture rather than pure n8n logic. Daily immutable snapshots, no intraday revisions. Task-count progress rather than effort-weighted progress. No critical-path scheduling, earned-value analysis, dependency-cycle detection, production source connectors or Power BI dashboard file. Optional AI performs fact ordering only. External sends may repeat after an acknowledgement-loss crash. No production authentication, scale benchmark, retention automation or automatic dead-letter replay.
