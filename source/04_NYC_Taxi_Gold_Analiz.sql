-- Databricks notebook source
-- MAGIC %md
-- MAGIC # NYC Taxi | Gold aggregation and Delta inspection
-- MAGIC 
-- MAGIC ## Goal
-- MAGIC Create a dashboard-ready day/hour table while separating volume counts from eligible-only distance and duration averages.
-- MAGIC 
-- MAGIC ## Setup
-- MAGIC Run notebook 02 first. Notebook 03 is read-only analysis and is optional for building Gold.
-- MAGIC 
-- MAGIC **Write behavior:** `CREATE OR REPLACE TABLE` fully refreshes the project Gold table from Silver. Existing Delta history is retained, so a rerun creates another version. Selected unchanged queries retain recorded output tables from the original export. Table-history/detail outputs were cleared because they included session and account metadata.
-- MAGIC 
-- MAGIC ## Steps
-- COMMAND ----------
-- MAGIC %md
-- MAGIC ### Create or refresh the Gold Delta table
-- COMMAND ----------
CREATE OR REPLACE TABLE workspace.default.nyc_taxi_gold_gun_saat_2025_01
USING DELTA
AS
SELECT
    CAST(tpep_pickup_datetime AS DATE) AS binis_tarihi,
    HOUR(tpep_pickup_datetime) AS binis_saati,

    COUNT(*) AS yolculuk_kaydi_sayisi,

    SUM(
        CASE WHEN olcum_analizine_uygun THEN 1 ELSE 0 END
    ) AS olcume_uygun_kayit_sayisi,

    AVG(
        CASE WHEN olcum_analizine_uygun THEN trip_distance END
    ) AS ortalama_mesafe_mil,

    AVG(
        CASE WHEN olcum_analizine_uygun THEN sure_dakika END
    ) AS ortalama_sure_dakika

FROM workspace.default.nyc_taxi_silver_2025_01
GROUP BY
    CAST(tpep_pickup_datetime AS DATE),
    HOUR(tpep_pickup_datetime);
-- COMMAND ----------
-- MAGIC %md
-- MAGIC ### Reconcile the monthly totals
-- COMMAND ----------
SELECT
    COUNT(*) AS ozet_satir_sayisi,
    MIN(binis_tarihi) AS ilk_tarih,
    MAX(binis_tarihi) AS son_tarih,
    SUM(yolculuk_kaydi_sayisi) AS toplam_yolculuk_kaydi,
    SUM(olcume_uygun_kayit_sayisi) AS toplam_uygun_kayit
FROM workspace.default.nyc_taxi_gold_gun_saat_2025_01;
-- COMMAND ----------
-- MAGIC %md
-- MAGIC ### Inspect the first day/hour rows
-- COMMAND ----------
SELECT *
FROM workspace.default.nyc_taxi_gold_gun_saat_2025_01
ORDER BY binis_tarihi, binis_saati
LIMIT 24;
-- COMMAND ----------
-- MAGIC %md
-- MAGIC ### Check Gold/Silver reconciliation and the day/hour grain
-- COMMAND ----------
WITH silver_counts AS (
    SELECT COUNT(*) AS total_records,
           SUM(CASE WHEN olcum_analizine_uygun THEN 1 ELSE 0 END) AS eligible_records
    FROM workspace.default.nyc_taxi_silver_2025_01
), gold_counts AS (
    SELECT COUNT(*) AS summary_rows,
           SUM(yolculuk_kaydi_sayisi) AS total_records,
           SUM(olcume_uygun_kayit_sayisi) AS eligible_records,
           COUNT(DISTINCT STRUCT(binis_tarihi, binis_saati)) AS unique_keys
    FROM workspace.default.nyc_taxi_gold_gun_saat_2025_01
)
SELECT
    g.summary_rows,
    g.summary_rows = g.unique_keys AS keys_are_unique,
    g.total_records = s.total_records AS volume_reconciles,
    g.eligible_records = s.eligible_records AS eligibility_reconciles
FROM gold_counts g CROSS JOIN silver_counts s;
-- COMMAND ----------
-- MAGIC %md
-- MAGIC ### Inspect Delta history
-- COMMAND ----------
DESCRIBE HISTORY workspace.default.nyc_taxi_gold_gun_saat_2025_01;
-- COMMAND ----------
-- MAGIC %md
-- MAGIC ### Inspect the current table details
-- COMMAND ----------
DESCRIBE DETAIL workspace.default.nyc_taxi_gold_gun_saat_2025_01;
-- COMMAND ----------
-- MAGIC %md
-- MAGIC ### Read the first retained Gold snapshot
-- COMMAND ----------
SELECT
    COUNT(*) AS ozet_satir_sayisi,
    SUM(yolculuk_kaydi_sayisi) AS toplam_yolculuk_kaydi,
    SUM(olcume_uygun_kayit_sayisi) AS toplam_uygun_kayit
FROM workspace.default.nyc_taxi_gold_gun_saat_2025_01
VERSION AS OF 0;
-- COMMAND ----------
-- MAGIC %md
-- MAGIC ## Checks and recorded baseline
-- MAGIC The original recorded Gold snapshot has 744 unique day/hour groups, from 2025-01-01 through 2025-01-31. Total volume is 3,475,204 records; eligible volume is 3,380,592.
-- MAGIC 
-- MAGIC `VERSION AS OF 0` reads the first retained snapshot, which can differ from the current version after input changes. A version number is table-specific. Historical reads also depend on retained data files.
-- MAGIC 
-- MAGIC **Rollup rule:** sum count columns. For an overall eligible mean, weight each hourly mean by `olcume_uygun_kayit_sayisi` (using only non-null means), or calculate directly from Silver. An unweighted average of hourly averages is not the monthly mean.
-- MAGIC 
-- MAGIC ## Next steps
-- MAGIC Use `sql/dashboard_dataset.sql` in the Databricks dashboard SQL editor and follow `docs/DASHBOARD.md`. Notebook 05 demonstrates mutation and restore on a separate one-row table.
