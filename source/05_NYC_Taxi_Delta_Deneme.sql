-- Databricks notebook source
-- MAGIC %md
-- MAGIC # NYC Taxi | Delta Time Travel and restore exercise
-- MAGIC 
-- MAGIC ## Goal
-- MAGIC Observe a value change, read the original snapshot, restore it, and inspect the history on a dedicated one-row demonstration table.
-- MAGIC 
-- MAGIC ## Setup
-- MAGIC Run notebook 04 first. Only `workspace.default.nyc_taxi_delta_deneme` is modified here. The Silver and Gold tables are read-only inputs for this exercise.
-- MAGIC 
-- MAGIC `CREATE TABLE IF NOT EXISTS` preserves version 0 on repeated runs. The expected baseline assumes this demo table was first created from the supplied January 2025 data (January 1, hour 0: 7,344 records). If an unrelated pre-existing table uses this name, use a new demo-table name consistently across all cells. Do not replace version 0 before this exercise.
-- MAGIC 
-- MAGIC The recorded comparison/restore outputs come from the original user execution. The history output was removed because it included account/session details.
-- MAGIC 
-- MAGIC ## Steps
-- COMMAND ----------
-- MAGIC %md
-- MAGIC ### Create the demonstration table once
-- COMMAND ----------
CREATE TABLE IF NOT EXISTS workspace.default.nyc_taxi_delta_deneme
USING DELTA
AS
SELECT
    binis_tarihi,
    binis_saati,
    yolculuk_kaydi_sayisi
FROM workspace.default.nyc_taxi_gold_gun_saat_2025_01
WHERE binis_tarihi = DATE '2025-01-01'
  AND binis_saati = 0;
-- COMMAND ----------
-- MAGIC %md
-- MAGIC ### Update the value and compare current data with version 0
-- COMMAND ----------
UPDATE workspace.default.nyc_taxi_delta_deneme
SET yolculuk_kaydi_sayisi = 8344
WHERE binis_tarihi = DATE '2025-01-01'
  AND binis_saati = 0;

SELECT
    'Güncel sürüm' AS veri_surumu,
    yolculuk_kaydi_sayisi
FROM workspace.default.nyc_taxi_delta_deneme

UNION ALL

SELECT
    'Sürüm 0' AS veri_surumu,
    yolculuk_kaydi_sayisi
FROM workspace.default.nyc_taxi_delta_deneme VERSION AS OF 0;
-- COMMAND ----------
-- MAGIC %md
-- MAGIC ### Restore the original data
-- COMMAND ----------
RESTORE TABLE workspace.default.nyc_taxi_delta_deneme
TO VERSION AS OF 0;

SELECT *
FROM workspace.default.nyc_taxi_delta_deneme;
-- COMMAND ----------
-- MAGIC %md
-- MAGIC ### Inspect the history
-- COMMAND ----------
DESCRIBE HISTORY workspace.default.nyc_taxi_delta_deneme;
-- COMMAND ----------
-- MAGIC %md
-- MAGIC ## Checks and recorded result
-- MAGIC | State | `yolculuk_kaydi_sayisi` |
-- MAGIC |---|---:|
-- MAGIC | Version 0 | 7,344 |
-- MAGIC | Current data after UPDATE | 8,344 |
-- MAGIC | Current data after RESTORE | 7,344 |
-- MAGIC 
-- MAGIC On the original first run, history showed version 0 = CREATE TABLE AS SELECT, version 1 = UPDATE, and version 2 = RESTORE. On reruns the version numbers increase; the creation is skipped. RESTORE creates a new version and preserves the existing history.
-- MAGIC 
-- MAGIC ## Completion
-- MAGIC The Delta exercise completes this project. Automated Jobs, streaming, and incremental ingestion are outside its delivered scope.
