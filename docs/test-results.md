# Executed test evidence

Python business rules and local HTTP service; NOT an n8n execution

Executed: 2026-09-23T11:49:26.814068+00:00

| Test | Expected | Actual |
|---|---|---|
| `test_hub.HTTPIntegration.test_http_pipeline` | Assertions pass | PASS |
| `test_hub.HTTPIntegration.test_invalid_ack_returns_422` | Assertions pass | PASS |
| `test_hub.HTTPIntegration.test_ollama_transport_failure` | Assertions pass | PASS |
| `test_hub.HTTPIntegration.test_unknown_route` | Assertions pass | PASS |
| `test_hub.Persistence.test_ai_invalid_response_fallback` | Assertions pass | PASS |
| `test_hub.Persistence.test_ai_unavailable` | Assertions pass | PASS |
| `test_hub.Persistence.test_ai_valid_permutation` | Assertions pass | PASS |
| `test_hub.Persistence.test_at_risk_pm_only` | Assertions pass | PASS |
| `test_hub.Persistence.test_changed_data_same_day_conflict` | Assertions pass | PASS |
| `test_hub.Persistence.test_concurrent_claims_unique` | Assertions pass | PASS |
| `test_hub.Persistence.test_critical_recipients_include_pmo` | Assertions pass | PASS |
| `test_hub.Persistence.test_csv_export_idempotent` | Assertions pass | PASS |
| `test_hub.Persistence.test_digest_counts_and_upsert` | Assertions pass | PASS |
| `test_hub.Persistence.test_duplicate_ack` | Assertions pass | PASS |
| `test_hub.Persistence.test_duplicate_execution` | Assertions pass | PASS |
| `test_hub.Persistence.test_empty_digest` | Assertions pass | PASS |
| `test_hub.Persistence.test_empty_queue` | Assertions pass | PASS |
| `test_hub.Persistence.test_fifth_failed_attempt_dead_letter` | Assertions pass | PASS |
| `test_hub.Persistence.test_final_expired_lease_dead_letter` | Assertions pass | PASS |
| `test_hub.Persistence.test_healthy_has_no_notification` | Assertions pass | PASS |
| `test_hub.Persistence.test_lease_expiry_recovery` | Assertions pass | PASS |
| `test_hub.Persistence.test_notification_failure_retained` | Assertions pass | PASS |
| `test_hub.Persistence.test_out_of_order_rejected` | Assertions pass | PASS |
| `test_hub.Persistence.test_partial_stage_recovery` | Assertions pass | PASS |
| `test_hub.Persistence.test_resolved_then_reopened_issue` | Assertions pass | PASS |
| `test_hub.Persistence.test_severity_change_new_episode` | Assertions pass | PASS |
| `test_hub.Persistence.test_stale_ack_rejected` | Assertions pass | PASS |
| `test_hub.Persistence.test_trends_computed_from_real_prior_snapshot` | Assertions pass | PASS |
| `test_hub.Persistence.test_unresolved_issue_dedup_across_days` | Assertions pass | PASS |
| `test_hub.Rules.test_ai_duplicate_fact_rejected` | Assertions pass | PASS |
| `test_hub.Rules.test_ai_fact_invention_rejected` | Assertions pass | PASS |
| `test_hub.Rules.test_at_risk` | Assertions pass | PASS |
| `test_hub.Rules.test_budget_forecast_overrun` | Assertions pass | PASS |
| `test_hub.Rules.test_closed_critical_risk_not_escalated` | Assertions pass | PASS |
| `test_hub.Rules.test_critical_dependency_override` | Assertions pass | PASS |
| `test_hub.Rules.test_critical_overdue_tasks` | Assertions pass | PASS |
| `test_hub.Rules.test_critical_risk_override` | Assertions pass | PASS |
| `test_hub.Rules.test_due_today_not_overdue` | Assertions pass | PASS |
| `test_hub.Rules.test_duplicate_source_id` | Assertions pass | PASS |
| `test_hub.Rules.test_empty_portfolio` | Assertions pass | PASS |
| `test_hub.Rules.test_forecast_below_actual_rejected` | Assertions pass | PASS |
| `test_hub.Rules.test_healthy` | Assertions pass | PASS |
| `test_hub.Rules.test_invalid_as_of` | Assertions pass | PASS |
| `test_hub.Rules.test_invalid_date` | Assertions pass | PASS |
| `test_hub.Rules.test_missing_required_field` | Assertions pass | PASS |
| `test_hub.Rules.test_missing_stakeholder_rejected` | Assertions pass | PASS |
| `test_hub.Rules.test_missing_tasks_not_healthy` | Assertions pass | PASS |
| `test_hub.Rules.test_nan_budget` | Assertions pass | PASS |
| `test_hub.Rules.test_orphan_reference` | Assertions pass | PASS |
| `test_hub.Rules.test_overdue_milestone` | Assertions pass | PASS |
| `test_hub.Rules.test_path_like_id_rejected` | Assertions pass | PASS |
| `test_hub.Rules.test_report_covers_every_required_section` | Assertions pass | PASS |
| `test_hub.Rules.test_unknown_status_rejected` | Assertions pass | PASS |
| `test_hub.Rules.test_zero_budget` | Assertions pass | PASS |
