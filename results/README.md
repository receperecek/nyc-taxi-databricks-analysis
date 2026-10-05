# Recorded result extracts

These files were extracted from the supplied Databricks notebook outputs. They are baseline evidence, not a fresh runtime execution or an independent recomputation of the raw Parquet data.

| File | Scope | Source |
|---|---|---|
| `observed_metrics.json` | Recorded monthly totals and quality observations | Notebook 02 cells 5–33, notebook 03 cell 3, notebook 04 cell 2 |
| `hourly_pickup_counts.csv` | All January records grouped into 24 pickup hours | Original notebook 03, cell 3 |
| `gold_first_day_sample.csv` | 24 rows for January 1 only; not the full 744-row Gold table | Original notebook 04, final query in cell 1 |

Sample counts reconcile to 90,188 total and 88,517 eligible records for January 1. Hourly counts reconcile to 3,475,204 monthly records. Eligibility observations reconcile to 3,380,592 eligible + 94,612 ineligible = 3,475,204.

The dashboard PDF was supplied by the project author; the preview PNG is a direct render of its single page. A PDF/PNG is static and does not preserve interactive filter behavior.
