# Setup and execution

## Databricks prerequisites

Use a Databricks workspace with Python notebooks, SQL cells, Delta managed tables, and Unity Catalog Volumes. The original export records a serverless Python environment and Databricks Runtime 19.8 in history outputs. A recent environment exposing `pyspark.sql.functions.timestamp_diff` is required: this function was introduced in PySpark 4.0.

Required project access: read the raw Volume, create/replace project tables in `workspace.default`, and modify the separate demonstration table. If your catalog/schema differ, update all fully qualified names and Volume paths consistently. No credentials are embedded in the project.

## Prepare the input files

Download the January 2025 Yellow Taxi Parquet and taxi-zone CSV linked in [DATA_SOURCES.md](DATA_SOURCES.md).

In Databricks, use a SQL cell or the Catalog interface to create the raw Volume if it is absent:

```sql
CREATE VOLUME IF NOT EXISTS workspace.default.nyc_taxi_raw;
```

Upload both files into that Volume. Notebook 02 expects:

```text
/Volumes/workspace/default/nyc_taxi_raw/yellow_tripdata_2025-01.parquet
/Volumes/workspace/default/nyc_taxi_raw/taxi_zone_lookup.csv
```

The raw Parquet is deliberately excluded from Git. The historical filename does not itself guarantee that every pickup falls in January; notebook 02 applies `[2025-01-01, 2025-02-01)` explicitly.

## Import and execute

Import each file from `notebooks/` using the Workspace import action. Set the default language to Python; the SQL cells carry `%sql` explicitly.

| Notebook | Role | Depends on |
|---|---|---|
| 01 | Optional sample-data PySpark lesson | `samples.nyctaxi.trips` |
| 02 | Raw ingestion, exploration, enrichment, Silver persistence | Uploaded Parquet and CSV |
| 03 | Read-only Silver analysis | Silver from 02 |
| 04 | Gold persistence and Delta inspection | Silver from 02 |
| 05 | Dedicated one-row Delta mutation/restore exercise | Gold from 04 |

Use **Run all** in each notebook, in order **02 → 03 → 04 → 05**. A notebook's Python variables must be initialized within that notebook, so run its setup and import cells first. No `%run` dependency on another notebook's in-memory DataFrame is required: cross-notebook dependencies use persistent tables.

For an alternate Databricks import, use `source/`. These are generated representations of the same notebook cells; choose one format rather than importing both copies as pipeline tasks.

## Refresh behavior

- Notebook 02: rebuilds Silver from the same fixed-month raw input using `CREATE OR REPLACE TABLE`.
- Notebook 04: rebuilds Gold from current Silver using `CREATE OR REPLACE TABLE`.
- Neither stage appends records; rerunning the same input should preserve the logical totals while adding Delta versions.
- Notebook 05: uses `CREATE TABLE IF NOT EXISTS` so its initial version 0 remains available. UPDATE and RESTORE add further versions on reruns. Only the dedicated demo table is mutated.

The Gold historical read targets version 0, the first retained snapshot. It is not guaranteed to match current totals after input or rule changes. The demonstration's 0/1/2 history sequence applies to its first run only. Historical reads require the old data files to remain available; do the tutorial promptly.

## Verify and reconstruct the dashboard

After running 02 and 04, execute the statements in `sql/validation_queries.sql`, one at a time in the SQL editor, or paste individual statements into `%sql` cells. For the original supplied input, compare the results with `docs/VALIDATION.md`.

Then follow [DASHBOARD.md](DASHBOARD.md). Filter state and chart selections affect visible counts; clear selections before comparing full-month totals.

## Optional local package validation

This checks exported files only; it does not run Databricks or access the raw dataset.

```bash
python -m pip install -r requirements-dev.txt
python scripts/check_package.py
```

If the sample table is unavailable in your workspace, skip notebook 01. The January 2025 pipeline is independent of it.
