# Data sources and provenance

## Primary January 2025 inputs

| Input | Authority / reference | Purpose |
|---|---|---|
| `yellow_tripdata_2025-01.parquet` | [TLC download](https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-01.parquet) | Yellow Taxi trip records |
| `taxi_zone_lookup.csv` | [TLC lookup](https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv) | Map LocationID to Borough and Zone |
| Field definitions | [Yellow Taxi dictionary](https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf) | Column meanings and category definitions |
| Dataset publication | [TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) | Source context and download index |

The original notebook reads these input filenames from a Unity Catalog Volume. It records 3,475,226 raw records and 265 unique zone lookup keys. The repository documents the official matching source files; it does not claim to have freshly downloaded or recomputed the full Parquet during packaging.

TLC states that the trip data comes from providers and does not guarantee its accuracy. The 2025 schema includes `cbd_congestion_fee`. Not all missing fields are invalid records: the recorded payment category 0 / null-rate-code association is inspected, and null rate codes are not an exclusion condition.

Pickup/drop-off values in the January Parquet are recorded as `timestamp_ntz` in the supplied schema. The analysis uses those local wall-clock values directly, without a UTC conversion. Do not reinterpret an export's `.000` representation as a new timezone conversion. January eligibility is determined by pickup time, even if a trip ends outside the month.

## Separate teaching sample

Notebook 01 reads `samples.nyctaxi.trips`. Its recorded schema and 2016 records differ from the January Parquet: it uses pickup/drop-off ZIP fields, whereas the TLC January pipeline joins LocationID values to named zones. The sample notebook's 21,932 records and 21,818 analysis subset are not inputs to the Gold table or dashboard.

## Evidence shipped with this repository

The author supplied five notebook exports with recorded outputs and one single-page dashboard PDF. Unchanged table outputs are retained in portable notebook output form; Databricks account/session metadata and error traces are removed. Modified cells have their stale outputs cleared. `results/` contains bounded extracts of the original output values.

The preview PNG is a rendering of the supplied dashboard PDF. It shows January counts and charts. Its date controls are blank in the PDF and are not interactive; the full-month totals reconcile to the notebook results. No fresh measurement period or live public dashboard URL is inferred from the export date.

## Technical references

- [Databricks notebook import/export](https://docs.databricks.com/aws/en/notebooks/notebook-export-import)
- [Databricks CREATE TABLE / REPLACE](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-ddl-create-table-using)
- [Delta history, Time Travel and RESTORE](https://docs.databricks.com/aws/en/tables/history)
- [PySpark timestamp_diff](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.functions.timestamp_diff.html)
