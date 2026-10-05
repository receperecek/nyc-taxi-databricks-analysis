-- Run each statement after notebooks 02 and 04 execute in Databricks.
-- Fixed-month baseline values are documented in docs/VALIDATION.md.
-- These queries read data; they do not modify project tables.

-- 1. Silver population and flag counts.
SELECT
    COUNT(*) AS january_records,
    SUM(CASE WHEN olcum_analizine_uygun THEN 1 ELSE 0 END) AS eligible_records,
    SUM(CASE WHEN NOT olcum_analizine_uygun THEN 1 ELSE 0 END) AS ineligible_records,
    SUM(CASE WHEN olcum_analizine_uygun IS NULL THEN 1 ELSE 0 END) AS null_flags,
    SUM(CASE WHEN tpep_pickup_datetime < TIMESTAMP '2025-01-01'
                  OR tpep_pickup_datetime >= TIMESTAMP '2025-02-01'
                  OR tpep_pickup_datetime IS NULL THEN 1 ELSE 0 END) AS outside_window
FROM workspace.default.nyc_taxi_silver_2025_01;

-- 2. Eligibility should match the documented predicate (zero mismatches).
SELECT COUNT(*) AS eligibility_mismatches
FROM workspace.default.nyc_taxi_silver_2025_01
WHERE NOT (olcum_analizine_uygun <=> COALESCE(
    trip_distance > 0 AND trip_distance <= 100
    AND sure_dakika > 0 AND sure_dakika <= 180
    AND ortalama_hiz_mph <= 80, FALSE
));

-- 3. Gold scope and unique date/hour keys.
SELECT
    COUNT(*) AS gold_rows,
    COUNT(DISTINCT STRUCT(binis_tarihi, binis_saati)) AS unique_date_hour_keys,
    MIN(binis_tarihi) AS first_date,
    MAX(binis_tarihi) AS last_date,
    SUM(yolculuk_kaydi_sayisi) AS all_records,
    SUM(olcume_uygun_kayit_sayisi) AS eligible_records
FROM workspace.default.nyc_taxi_gold_gun_saat_2025_01;

-- 4. Gold constraints should have zero violations.
SELECT COUNT(*) AS invalid_gold_rows
FROM workspace.default.nyc_taxi_gold_gun_saat_2025_01
WHERE binis_tarihi IS NULL OR binis_saati IS NULL
   OR binis_saati NOT BETWEEN 0 AND 23
   OR binis_tarihi NOT BETWEEN DATE '2025-01-01' AND DATE '2025-01-31'
   OR yolculuk_kaydi_sayisi IS NULL OR olcume_uygun_kayit_sayisi IS NULL
   OR yolculuk_kaydi_sayisi <= 0 OR olcume_uygun_kayit_sayisi < 0
   OR olcume_uygun_kayit_sayisi > yolculuk_kaydi_sayisi;

-- 5. Reconcile volume and eligible counts to current Silver.
WITH s AS (
    SELECT COUNT(*) AS total_records,
           SUM(CASE WHEN olcum_analizine_uygun THEN 1 ELSE 0 END) AS eligible_records
    FROM workspace.default.nyc_taxi_silver_2025_01
), g AS (
    SELECT SUM(yolculuk_kaydi_sayisi) AS total_records,
           SUM(olcume_uygun_kayit_sayisi) AS eligible_records
    FROM workspace.default.nyc_taxi_gold_gun_saat_2025_01
)
SELECT g.total_records - s.total_records AS volume_difference,
       g.eligible_records - s.eligible_records AS eligibility_difference
FROM g CROSS JOIN s;

-- 6. January 1 dashboard filter check: 90,188 / 88,517 in the original run.
SELECT SUM(yolculuk_kaydi_sayisi) AS january_1_records,
       SUM(olcume_uygun_kayit_sayisi) AS january_1_eligible_records
FROM workspace.default.nyc_taxi_gold_gun_saat_2025_01
WHERE binis_tarihi = DATE '2025-01-01';

-- 7. All-month hourly volumes; compare with results/hourly_pickup_counts.csv.
SELECT binis_saati, SUM(yolculuk_kaydi_sayisi) AS yolculuk_kaydi_sayisi
FROM workspace.default.nyc_taxi_gold_gun_saat_2025_01
GROUP BY binis_saati
ORDER BY binis_saati;
