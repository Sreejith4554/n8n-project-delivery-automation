# Windows / Docker Desktop setup

This guide assumes an existing self-hosted n8n Community Edition instance at `http://localhost:5678` and an existing Docker volume named `n8n_data`. No n8n Cloud subscription, Python installation or paid API is required for the Docker path. Python and Node.js are needed only to run the optional host-side developer tests.

## 1. Extract and inspect the existing instance

Extract the ZIP. Open PowerShell in the extracted `n8n-project-delivery-automation` directory (the folder containing `compose.yaml`). Start Docker Desktop.

```powershell
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}"
$ExistingN8n = Read-Host "Enter the name of your existing n8n container"
docker inspect --format '{{.Config.Image}}' $ExistingN8n
docker exec $ExistingN8n n8n --version
docker inspect --format '{{range .Mounts}}{{println .Name .Destination}}{{end}}' $ExistingN8n
docker volume inspect n8n_data
```

Verify the mounted volume at `/home/node/.n8n` really is `n8n_data`. If it is different, update the external volume name in Compose to the actual volume. Stop here if your current instance uses PostgreSQL, an externally supplied `N8N_ENCRYPTION_KEY`, a custom user folder, or other essential settings until those same settings are included in the new Compose service. This repository's default is a local SQLite-backed n8n instance. **Do not replace an existing encryption key.** An external database requires its own consistent backup as well.

The exports were checked against source definitions at **n8n 2.40.5**. Your installed version is not known. Use the exact existing image in `.env` to avoid an unintended upgrade, then perform the import smoke test. If it cannot support these node versions, test 2.40.5 with a fresh separate volume before planning an upgrade. The reference release is not a claim of testing your installation or a promise that it remains the newest release.

## 2. Stop and back up before reusing the existing volume

Do not run two n8n processes against the same SQLite volume. The commands below stop the existing container without removing it, then create a read-only backup. The helper Alpine container may be downloaded on first use.

```powershell
docker stop $ExistingN8n
New-Item -ItemType Directory -Force backups | Out-Null
$BackupDirectory = (Resolve-Path backups).Path
$BackupName = "n8n_data-$(Get-Date -Format yyyyMMdd-HHmmss).tgz"
docker run --rm --mount "type=volume,source=n8n_data,target=/source,readonly" --mount "type=bind,source=$BackupDirectory,target=/backup" alpine:3.22 sh -c "tar czf /backup/$BackupName -C /source ."
Get-Item "backups/$BackupName"
```

Check Docker exited successfully and the backup exists before starting Compose. Keep the archive private: it contains workflows, encryption configuration and potentially sensitive execution data. Leave the original container stopped while this Compose instance uses its volume. If the original was managed by another Compose project, keep that project's configuration for rollback; do not start both projects together.

**Separate evaluation option:** to leave your existing instance running, change the new Compose host port to `127.0.0.1:5679:5678`, change `volumes.n8n_data.name` to `pmo_demo_n8n_data`, and run `docker volume create pmo_demo_n8n_data`. Then use `http://localhost:5679` and the reference image. This creates a new n8n owner account and does not reuse your saved credentials. The default repository intentionally reuses `n8n_data` as requested.

## 3. Configure and start

```powershell
Copy-Item .env.example .env
notepad .env
New-Item -ItemType Directory -Force output | Out-Null
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose logs --tail=50 hub-api
docker compose exec hub-api python -c "import json,urllib.request; print(json.load(urllib.request.urlopen('http://localhost:8000/health')))"
```

Set `N8N_IMAGE` to the exact image chosen in step 1. Keep `DEMO_AS_OF=2026-09-23`, `NOTIFICATION_MODE=dry-run`, `OLLAMA_ENABLED=false`. No real addresses or secrets are needed. The `hub-api` image runs as UID 10001. Docker Desktop normally handles bind-mount permissions. If it cannot write `/output`, check Windows file-sharing permissions and that the folder exists. Linux users must give UID 10001 write access to the host output folder.

The existing external volume survives Compose teardown. The companion service uses a separate `hub_state` named volume. Never use `docker compose down -v` as routine cleanup: it removes companion state. Use `docker compose down` to stop the project. Never remove `n8n_data` to reset this demo.

## 4. Import order — exactly six files

At `http://localhost:5678`, create/open a workflow and use the workflow menu → **Import from File**, select the file and save it. Repeat separately in this order:

1. `workflows/01-project-health-monitor.json`
2. `workflows/02-risk-escalation.json`
3. `workflows/03-ai-status-report.json`
4. `workflows/04-stakeholder-notification.json`
5. `workflows/05-weekly-pmo-digest.json`
6. `workflows/06-analytics-pipeline.json`

Import each once. Re-importing can create another workflow; leave only one active copy of each. They arrive inactive. No cross-workflow ID references or credential IDs need to be edited. HTTP URLs use `http://hub-api:8000`, which resolves **inside Docker**; do not change it to `localhost` in an n8n node.

If n8n displays an unsupported node/version or parameter warning, record your n8n version and the node, and resolve it before activation. Static JSON checks do not substitute for this import check. Workflow 04 intentionally has disabled native SMTP and Slack nodes; that is expected in simulation mode.

## 5. Manual acceptance run

Execute **01 → 02 → 03 → 04 → 06 → 05** using each workflow's manual trigger.

- 01 seeds the prior synthetic day once and creates ten current snapshots. Repeating it returns `duplicate: true`, with no additional snapshots.
- 02 consumes 20 snapshots in chronological order and stores exception episodes.
- 03 creates 20 reports and only eligible At Risk/Critical outbox items.
- 04 claims and simulates **one** notification per run; its simulation acknowledgement should succeed. Run it again to see another item. Empty queue means the HTTP node emits no items; downstream nodes do not execute.
- 06 produces `output/portfolio-health.csv`, `output/escalations.json`, and 20 Markdown reports in `output/reports/`.
- 05 produces `output/weekly-digest.md` and `.json`. Current-day totals must be 10 projects: 3 Healthy, 2 At Risk, 5 Critical.

Compare with `examples/`. Processing timestamps and lease UUIDs will differ. Run 01–03 again and confirm record counts remain unchanged. Restart `hub-api` and repeat to check persistence.

After the checks pass, activate/publish the workflows using the controls in your installed n8n version. Schedules run only when active. Allow one minute per notification to drain the initial demo outbox. All schedules use Europe/Berlin. Keep the date frozen for a repeatable portfolio demo.

## 6. Optional local Ollama

The deterministic report is the complete core implementation. To try constrained AI assistance, install/run Ollama locally and pull a model, for example:

```powershell
ollama pull llama3.2:3b
```

Ensure Ollama is reachable from Docker at `http://host.docker.internal:11434`. Depending on your installation, its bind address must be adjusted (`OLLAMA_HOST`) and its process restarted. If binding beyond loopback, use Windows Firewall to limit access to the local/Docker host; do not expose an unauthenticated model API to your LAN or the internet.

Set `OLLAMA_ENABLED=true` in `.env`; keep `OLLAMA_MODEL` equal to the model you pulled, then:

```powershell
docker compose up -d hub-api
```

Reports already persisted for a date are deliberately not regenerated. Test the optional path with a **new companion state volume** or a later synthetic snapshot date. Change `volumes.hub_state` to include a fresh explicit `name`, such as `pmo_hub_ai_demo_state`, stop the project with `docker compose down`, and start it again; do not delete `n8n_data`. The original state volume remains available. A cold or slow model may exceed the eight-second timeout and legitimately trigger deterministic fallback. No actual Ollama inference was executed in the build environment.

## 7. Optional SMTP or Slack delivery

Configure **one channel at a time**. This is not required for the portfolio core. Use your own test inboxes or a private test channel only.

1. In n8n create the chosen credential. SMTP: host, port, username/password and appropriate TLS settings. Slack: a bot credential with permission to post in the selected private test channels, and invite the bot to those channels.
2. In workflow 04 select the credential on the chosen native send node. For email, replace the `demo-sender@example.invalid` sender with an authorized sender. Replace recipient values in `data/stakeholders.csv` with your own consenting test addresses **before creating that date's snapshots**, or use a fresh companion volume. The `.invalid` addresses intentionally cannot deliver.
3. For Slack, replace both `REPLACE_PM_CHANNEL_ID` and `REPLACE_PMO_CHANNEL_ID` in the Channel expression with real test channel IDs. The PM channel must include the PM; the Critical channel must include both the PM and simulated PMO reviewer. The node routes by severity.
4. Enable the selected send node; leave the unused send node disabled. Change `ENABLE_LIVE_DELIVERY` to `true` in the **Live delivery gate** Code node. Save the workflow. Do not enable the gate while the chosen send node remains disabled: disabled n8n nodes pass data through.
5. Set `NOTIFICATION_MODE=email` or `slack` in `.env`, then `docker compose up -d hub-api`.
6. Use a fresh eligible notification (a new state volume/date). A simulated item is terminal and is not silently replayed to a real provider. Manually execute 04 and verify receipt, success acknowledgement and no duplicate on repeat.
7. Temporarily use an invalid test-provider configuration to verify the failure branch, retry delay and retained outbox item. Restore it afterwards. Never perform this with production recipients.

The chosen node's credentials stay inside n8n; no credentials are present in this repository. Exports omit credential references rather than inventing fake IDs. Credential selection in these two nodes is the placeholder configuration step.

## 8. Power BI Desktop

Get Data → Text/CSV → select `output/portfolio-health.csv`. Use UTF-8 and a comma delimiter. Set snapshot_date to Date, score/count fields to Whole Number, percentages to Decimal Number, remaining fields to Text. Leave initial previous score/change blank as null; do not coerce them to zero. Suggested visuals: project status count filtered to one snapshot date, score by project over time, and exception counts.

See `analytics-powerbi.md` for field mapping and example measures. The repository supplies a dataset, not a `.pbix` file, a gateway, DirectQuery, or automatic Power BI Service refresh.

## 9. Troubleshooting and rollback

- Port 5678 in use: stop the original container or use the separate evaluation port.
- `n8n_data` missing: confirm the actual existing volume name. A new user without an existing instance may create it with `docker volume create n8n_data`; this user-specific guide does not create it automatically.
- `hub-api` cannot resolve: n8n must be the Compose service on the same project network, not the old standalone container.
- Validation 422: inspect file headers, required fields, dates, IDs and enum spelling; fix the source. Changed input on an already saved date needs a new date or fresh demo state.
- Repeated failures: check n8n execution error details and `/health` counts via `docker compose exec`. `dead` notifications require provider reconciliation and a deliberate state-level repair; no automatic replay is provided.
- No scheduled runs: verify saved/published workflow state and timezone. Manual execution alone does not activate a schedule.
- Rollback: `docker compose down`, confirm the new n8n container stopped, then `docker start $ExistingN8n` only if no incompatible n8n migration occurred. If you deliberately upgraded n8n, restore the matching backup/image through a tested recovery procedure; do not downgrade blindly over a migrated database.

**REQUIRES LOCAL N8N VALIDATION:** every Docker, visual-import, scheduler, native integration and Ollama step above. The accompanying tests demonstrate the Python service separately and do not assert these local checks were completed.
