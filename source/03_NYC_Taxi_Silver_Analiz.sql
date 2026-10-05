-- Databricks notebook source
-- MAGIC %md
-- MAGIC # NYC Taxi | Silver analysis
-- MAGIC 
-- MAGIC ## Goal
-- MAGIC Compare eligible pickup groups and inspect the pickup-hour distribution for January 2025.
-- MAGIC 
-- MAGIC ## Setup
-- MAGIC Run notebook 02 first. This notebook reads `workspace.default.nyc_taxi_silver_2025_01` and creates no Gold table. Recorded outputs from unchanged queries are retained.
-- MAGIC 
-- MAGIC **Population:** borough and Queens comparisons use measurement-eligible records; the hourly volume query includes all January records.
-- MAGIC 
-- MAGIC ## Steps
-- COMMAND ----------
-- MAGIC %md
-- MAGIC ### Compare pickup boroughs
-- COMMAND ----------
SELECT
    pickup_borough,
    COUNT(*) AS secilen_yolculuk_sayisi,
    ROUND(AVG(trip_distance), 2) AS ortalama_mesafe_mil,
    ROUND(AVG(sure_dakika), 2) AS ortalama_sure_dakika
FROM workspace.default.nyc_taxi_silver_2025_01
WHERE olcum_analizine_uygun = true
GROUP BY pickup_borough
ORDER BY secilen_yolculuk_sayisi DESC;
-- COMMAND ----------
-- MAGIC %md
-- MAGIC ### Inspect the top Queens pickup zones
-- COMMAND ----------
SELECT
    pickup_zone,
    COUNT(*) AS yolculuk_sayisi,
    ROUND(AVG(trip_distance), 2) AS ortalama_mesafe_mil,
    ROUND(AVG(sure_dakika), 2) AS ortalama_sure_dakika
FROM workspace.default.nyc_taxi_silver_2025_01
WHERE olcum_analizine_uygun = true
  AND pickup_borough = 'Queens'
GROUP BY pickup_zone
ORDER BY yolculuk_sayisi DESC
LIMIT 10;
-- COMMAND ----------
-- MAGIC %md
-- MAGIC ### Compare Queens airports with other Queens zones
-- COMMAND ----------
SELECT
    CASE
        WHEN pickup_zone IN ('JFK Airport', 'LaGuardia Airport')
            THEN 'Havalimanı'
        ELSE 'Queens diğer bölgeler'
    END AS binis_grubu,
    COUNT(*) AS yolculuk_sayisi,
    ROUND(AVG(trip_distance), 2) AS ortalama_mesafe_mil,
    ROUND(AVG(sure_dakika), 2) AS ortalama_sure_dakika
FROM workspace.default.nyc_taxi_silver_2025_01
WHERE olcum_analizine_uygun = true
  AND pickup_borough = 'Queens'
GROUP BY 1;
-- COMMAND ----------
-- MAGIC %md
-- MAGIC ### Count all January records by pickup hour
-- COMMAND ----------
SELECT
    HOUR(tpep_pickup_datetime) AS binis_saati,
    COUNT(*) AS yolculuk_kaydi_sayisi
FROM workspace.default.nyc_taxi_silver_2025_01
GROUP BY binis_saati
ORDER BY binis_saati;
-- COMMAND ----------
-- MAGIC %md
-- MAGIC ## Checks and takeaways
-- MAGIC Recorded outputs show:
-- MAGIC - Manhattan: 3,013,431 measurement-eligible pickup records; mean distance 2.28 miles and mean duration 12.78 minutes.
-- MAGIC - Queens: 283,713 eligible pickup records; mean distance 12.02 miles and mean duration 31.45 minutes.
-- MAGIC - JFK and LaGuardia together: 231,080 of the eligible Queens pickup records.
-- MAGIC - Highest month-wide pickup-hour total: 18:00–18:59, with 267,951 records.
-- MAGIC - Lowest month-wide pickup-hour total: 04:00–04:59, with 20,033 records.
-- MAGIC 
-- MAGIC These are descriptive associations. Airport mix may help interpret the Queens averages; this notebook does not establish a causal effect or measure traffic congestion.
-- MAGIC 
-- MAGIC ## Next steps
-- MAGIC Gold creation and reconciliation are owned only by notebook 04.
