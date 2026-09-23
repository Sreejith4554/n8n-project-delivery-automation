# Security

## Credentials and environment

No API keys, passwords, tokens, webhook secrets, personal addresses or real company records are included. Exported native email/Slack nodes have no `credentials` object; select your own n8n credential after import. They are disabled by default and additionally gated. Do not paste provider secrets into Code nodes, CSVs or workflow parameters. `.env.example` contains nonsecret configuration only; `.env`, databases, logs, output, backups and ZIPs are ignored by Git.

Reuse the existing n8n encryption configuration and persistent volume. Preserve an externally configured encryption key exactly. Losing it can make credentials unrecoverable. n8n credential encryption does not make execution data and backups safe to publish.

## Network and webhook security

There are no webhook triggers in this version. All stages run from schedules/manual execution. No publicly reachable callback, unauthenticated public ingestion URL or secret-bearing webhook is needed.

n8n is bound to host loopback (`127.0.0.1:5678`); plain HTTP and `N8N_SECURE_COOKIE=false` are solely for this local setup. `hub-api` publishes no host port. It has **no application authentication** and trusts the Compose network. Other trusted local containers or privileged host users may be able to reach it. Do not connect untrusted containers to that network. A public or team deployment must add authentication, TLS, network segmentation and access controls before use.

If push/webhook ingestion is added later, authenticate requests, verify signatures and replay windows, validate payload size/schema, rate-limit and constrain source permissions. Those controls are future work, not implemented features.

## Least privilege and PII minimization

The Python container runs non-root with a read-only root filesystem, dropped Linux capabilities and no-new-privileges. Only `/state`, `/output` and temporary storage are writable. Source data mounts are read-only. n8n file access is restricted to `/files`; it needs no host shell or external module access. Do not disable n8n safeguards to run this project.

Use a restricted SMTP identity and dedicated Slack bot in test channels. At Risk includes PM only; Critical includes PM and PMO. The examples use reserved `.invalid` addresses and simulated role names. If adapting the project, collect only necessary project metadata and contact details, and get permission before sending real messages.

Optional Ollama receives project fact text. Keep its endpoint local and access-restricted. The application ignores model prose and only accepts verified fact IDs. This bounds factual output but is not a claim of general prompt-injection immunity for future extended agents.

## Logging, state and backups

n8n execution data can contain report content and recipients; the Compose example sets seven-day execution retention. The local database records sanitized error categories and stores project history/report payloads. SQLite has no built-in at-rest encryption here and no automatic retention policy. Use OS disk encryption and a documented retention/deletion process before real data use. Back up n8n and hub state consistently, protect backups, and test recovery.

No sensitive HTTP payloads are logged by the Python request handler. Exceptions returned for validation can include synthetic IDs. Avoid adding raw record logging. Test evidence and examples contain synthetic content only.

## GitHub protection

Before publishing, review `git diff --cached` and the full file list; ensure `.env`, `output/`, `state/`, backups and exported real n8n credentials are excluded. Enable repository secret scanning/push protection where available, and run a current secret scanner locally. The build audit performs focused pattern checks; it is not a guarantee against all possible secrets. Never upload a real n8n volume or database.

## Production considerations

This is a portfolio implementation, not a production certification. Before real deployment: supported patched and pinned images/digests, dependency review, authenticated service boundaries, TLS, threat model, schema migrations, retention policy, backups/restore drills, monitoring, dead-letter remediation, provider-specific idempotency, load tests, RBAC and human approval of consequential decisions. None of those organizational assurances should be inferred from the demonstration.
