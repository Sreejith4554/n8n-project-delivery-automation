# Analytics dataset and Power BI

`06-analytics-pipeline.json` invokes the local service to export all saved snapshots to `output/portfolio-health.csv`. The sample has 20 rows across 2026-09-22 and 2026-09-23. No Power BI subscription is required to consume the CSV in Desktop.

| Field | Type | Definition |
|---|---|---|
| snapshot_date | Date | Immutable business date |
| project_id | Text | Synthetic stable project identifier |
| project_name | Text | Synthetic display name |
| project_manager | Text | Simulated accountable PM |
| project_status | Text | HEALTHY / AT RISK / CRITICAL |
| health_score | Whole number | Final score after penalties and caps |
| progress_percentage | Decimal | Completed task count / all task count ×100 |
| overdue_tasks | Whole number | Open or in-progress work due before snapshot |
| total_tasks | Whole number | All project tasks |
| high_risks | Whole number | Unresolved high plus critical risks |
| blocked_dependencies | Whole number | All blocked dependencies |
| milestone_variance_days | Whole number | Maximum variance of an open milestone |
| budget_variance_percentage | Decimal | Forecast at completion versus baseline |
| previous_health_score | Nullable whole number | Previous available snapshot's score |
| health_score_change | Nullable whole number | Current minus previous score |
| trend | Text | NEW / STABLE / IMPROVING / DETERIORATING |

Logical key: project_id + snapshot_date. When counting current portfolio status, filter to a single date; otherwise project-day rows double-count the portfolio. These percentages are on a 0–100 scale: format as decimal with a percent suffix or divide by 100 before using Power BI's Percentage format.

Suggested basic DAX after naming the imported table `PortfolioHealth`:

```dax
Projects = DISTINCTCOUNT(PortfolioHealth[project_id])
Critical Projects =
CALCULATE([Projects], PortfolioHealth[project_status] = "CRITICAL")
Average Health = AVERAGE(PortfolioHealth[health_score])
Overdue Tasks = SUM(PortfolioHealth[overdue_tasks])
```

These measures depend on an appropriate date filter; they do not automatically select the latest snapshot. Use snapshot_date as a single-select slicer for a simple demo. Use a line chart by date and project for trends. Do not sum health scores, percentages or repeated weekly project counts.

CSV data is generated and tested. The DAX examples are guidance and were not executed in Power BI. No `.pbix`, cloud refresh schedule or on-premises data gateway is supplied.
