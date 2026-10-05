# Verification status

## What was verified during packaging

- The five supplied notebook files and the five curated notebook files validate as nbformat v4.
- Python cells and generated Python source compile after handling Databricks magic cells separately.
- SELECT/DDL SQL syntax is checked with a Databricks-dialect parser. The parser does not support DESCRIBE DETAIL and RESTORE; those canonical command structures are checked separately. Neither check substitutes for Databricks execution.
- Silver eligible + ineligible totals reconcile to the January population.
- The 24 recorded hourly counts reconcile to the monthly total.
- The 24 recorded January 1 Gold sample rows reconcile to the observed daily counters.
- The single-page supplied PDF was rendered and visually reviewed; its two counters match the recorded notebook totals.
- README/doc local links and image references resolve, and generated source exports match their notebook cells.
- Error traces and Databricks account/session metadata were removed from the curated files. Unchanged portable output tables remain recorded evidence.

## Execution boundary

**The edited notebook package has not been executed end-to-end in Databricks during packaging.** This environment has no Databricks `spark`, Unity Catalog Volume, or live project tables. The recorded outputs establish the original user-run results; static checks establish file structure and syntax, not successful execution of the edited runtime path.

The curated notebooks could not be visually opened in a notebook viewer here (no Databricks/notebook renderer is available). The dashboard PDF was visually reviewed separately. After import, open each saved notebook in Databricks and inspect its section order, tables, labels, and output sizes after Run all.

Edited cells have stale outputs cleared. New lookup/row-count assertions and SQL reconciliation checks must be executed in the target workspace. The main changes are documented in [PACKAGING_CHANGES.md](PACKAGING_CHANGES.md).

## Target-workspace verification

1. Follow SETUP.md and run notebooks 02, 03, and 04 top to bottom.
2. Execute each statement in `sql/validation_queries.sql`.
3. Run notebook 05 and verify current/old values before and after RESTORE.
4. Reconstruct the dashboard and check the full-month and January 1 counters.

For the original supplied input, expect:

| Check | Baseline |
|---|---:|
| Raw records | 3,475,226 |
| January / Silver records | 3,475,204 |
| Eligible records | 3,380,592 |
| Ineligible records | 94,612 |
| Candidate records | 3,381,449 |
| Candidate speeds >80 mph | 857 |
| Gold rows and distinct keys | 744 / 744 |
| Gold min / max date | 2025-01-01 / 2025-01-31 |
| Gold all-record total | 3,475,204 |
| Gold eligible total | 3,380,592 |
| January 1 total / eligible | 90,188 / 88,517 |
| Eligibility predicate mismatch count | 0 expected after rerun |
| Gold/Silver count mismatches | 0 expected after rerun |
| Invalid Gold hour / count constraints | 0 expected after rerun |

The final three checks are explicit acceptance checks in the packaged queries; they were not claimed as newly executed Databricks results. Baseline values are observations from the supplied exports and may differ if upstream data is revised.

## Delta demonstration

On the first run: version 0 holds 7,344, UPDATE changes current data to 8,344, and RESTORE returns current data to 7,344 as a new version. Recorded first-run history was CREATE TABLE AS SELECT → UPDATE → RESTORE, versions 0/1/2.

On reruns `IF NOT EXISTS` skips creation and subsequent writes add versions, so do not assert that the latest version must always equal 2. The production Gold table is not restored or updated by the demonstration.

## Local check command

```bash
python -m pip install -r requirements-dev.txt
python scripts/check_package.py
```

This validates the repository package only. A passing local check is not a successful Databricks pipeline run.
