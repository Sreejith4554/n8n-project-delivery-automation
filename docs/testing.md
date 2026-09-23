# Test plan and evidence

## Executed scope

Run `python -m unittest discover -s tests -v` for the Python rules, persistent state and local HTTP pipeline. Run `python scripts/check_workflows.py` with Node.js installed for JSON structure, unique names/IDs, connection targets, selected node versions, Code syntax and acknowledgement-expression checks. These are focused static checks, **not the complete n8n runtime schema validator**.

`python scripts/test_report.py` runs the real assertions and writes `test-results.json` and `test-results.md`. Those files contain the exact executed count and expected-versus-actual results. Source code, not the report wording, defines each assertion.

| Scenario | Expected result | Actual evidence |
|---|---|---|
| Healthy P01 | Score 100; no notification | Rules and persistence tests pass |
| At-risk P02 | AT RISK; PM only | Rules and recipient tests pass |
| Critical P03 | CRITICAL; nine overdue tasks | Rules test passes |
| Overdue P10 milestone | Six-day variance; escalation | Rules test passes |
| Blocked critical P04 dependency | Score capped at 59 | Rules test passes |
| Unresolved critical P06 risk | Score capped at 59; L2 escalation | Rules test passes |
| P05 forecast overrun | 30% variance; Critical | Rules test passes |
| Missing/malformed data | Reject before writing healthy result | Validation tests pass |
| Duplicate run and concurrent claims | Counts unchanged; unique claims | Persistence tests pass |
| AI unavailable/invalid | Complete deterministic fallback | Injected failure tests pass |
| Valid AI fact permutation | Only verified facts rendered | Adapter contract test passes |
| Notification failure | Retain pending item with backoff; dead after limit | Outbox tests pass; actual provider failure is local-only |
| Partial workflow failure/restart | Resume after durable stage boundary | Persistence test passes |
| Empty data/queue | No false healthy record or send | Empty-state tests pass |
| End-to-end service HTTP | 20 snapshots, reports, simulation, CSV/digest | Local HTTP server test passes |

Tests never contact SMTP or Slack, never send messages and never connect to the user's n8n instance. Model timeout/invalid-output paths are simulated. The HTTP integration test really starts a local Python HTTP server and calls its endpoints; it is not an n8n execution.

## REQUIRES LOCAL N8N VALIDATION

Record your actual version and date beside each completed check. Do not mark these passed based on the build-environment tests.

| Check | Procedure | Expected | Local result |
|---|---|---|---|
| Docker configuration/build | `docker compose config --quiet`, then build/start | Healthy companion service; n8n UI opens | NOT RUN |
| All six imports | Import each separately and inspect | Recognized node types; valid parameters; no active schedules initially | NOT RUN |
| Manual pipeline | 01,02,03,04,06,05 | Expected counts and exported files | NOT RUN |
| Simulation branch | Run 04 with defaults | No external send; simulated acknowledgement | NOT RUN |
| Empty outbox | Drain queue and run 04 again | No downstream send/ack | NOT RUN |
| Duplicate execution | Run 01–03 again | Same snapshots/reports/escalation totals | NOT RUN |
| Volume persistence | Restart both services and rerun | Original state and credentials remain | NOT RUN |
| Schedules | Activate/publish, inspect executions | Minute consumers and expected Berlin times | NOT RUN |
| SMTP success/failure | Configure safe inbox; valid then invalid credentials | Delivery+ack or error branch+retained item | NOT RUN |
| Slack success/failure | Configure private test channels | Severity routing and retained failures | NOT RUN |
| Actual Ollama | Warm model, fresh state/date, enable adapter | Valid ordering or documented fallback | NOT RUN |
| Power BI import | Import history CSV | Date/numeric types and single-date totals correct | NOT RUN |

## Reproducibility

`python scripts/generate_data.py` recreates both fixture directories deterministically. `python scripts/generate_workflows.py` recreates workflow files using stable UUIDs. `python scripts/demo.py` uses isolated temporary state and writes output files without touching Docker volumes. Processing timestamps are intentionally real UTC timestamps, so byte-for-byte comparison excludes those fields.

GitHub Actions configuration is supplied for unit tests, workflow checks, Compose config validation and a container build. It has not run on GitHub during this task. Docker is absent from the build environment; do not infer a successful container build from the presence of the CI file.
