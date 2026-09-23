# Five-minute demonstration

Prerequisite: finish the local import smoke tests and Docker setup. Keep dry-run mode. For a first-run story, use a fresh **companion** state volume; retain `n8n_data`. This script never sends real messages.

| Time | Show | Say / verify |
|---|---|---|
| 0:00–0:40 | README and CSV folder | “This is synthetic portfolio work: ten projects and 120 tasks. n8n orchestrates; the Python service owns transparent rules and durable state.” |
| 0:40–1:25 | Workflow 01, manual execution | “The service rejects bad data before scoring. Critical risks and dependencies override a superficially good score.” Check ten current snapshots, plus ten seeded prior snapshots. |
| 1:25–2:10 | Workflows 02 and 03, run manually | “Escalation episodes have owners, impact, required actions and due dates. Reports use verified facts; optional AI can only order them.” |
| 2:10–2:55 | Workflow 04, execute once | “Healthy means record only. At Risk goes to PM, Critical includes PMO. Here delivery is simulated; the real nodes are disabled.” Inspect the claimed item and simulation acknowledgement. |
| 2:55–3:40 | Execute 06 then 05; open output files | Show `output/reports/2026-09-23-P06.md` and `weekly-digest.md`: three Healthy, two At Risk, five Critical. River improves; Beacon deteriorates. |
| 3:40–4:20 | Run 01–03 again, service health counts | “Repeated execution does not duplicate daily snapshots, issue episodes or reports. An existing same-day snapshot also cannot silently change.” |
| 4:20–5:00 | CSV, executed tests and audit | “The CSV has two dates for trend analysis. Tests cover invalid input, provider failures and concurrent claims. This is local portfolio engineering, with no employer deployment or measured savings claimed.” |

If asked about delivery guarantees: the outbox prevents ordinary retry duplicates and concurrent claims, but a crash after external acceptance can still cause another send. Exactly-once provider delivery is not claimed.

If asked to show AI: explain the fallback first. Enable and warm Ollama before the session and use a new state/date; do not make the five-minute demo depend on model availability. Without a locally verified model, say “optional adapter implemented; local inference not yet demonstrated.”

Capture genuine n8n screenshots only after executing the local acceptance checks. Keep personal contact and credential screens out of recordings.
