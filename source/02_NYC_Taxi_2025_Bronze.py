# Databricks notebook source
# MAGIC %md
# MAGIC # NYC Taxi | January 2025 raw ingestion and Silver preparation
# MAGIC 
# MAGIC ## Goal
# MAGIC Read externally sourced TLC files, preserve January records, enrich locations, flag measurement suitability, and persist a Silver Delta table.
# MAGIC 
# MAGIC ## Setup
# MAGIC Upload these two files into `/Volumes/workspace/default/nyc_taxi_raw/` before running:
# MAGIC - `yellow_tripdata_2025-01.parquet`
# MAGIC - `taxi_zone_lookup.csv`
# MAGIC 
# MAGIC See [the TLC source page](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page). The raw files are the Bronze input; this notebook does **not** create a separate Bronze Delta table. The historical filename is retained.
# MAGIC 
# MAGIC The project counts records, not unique passengers. All January records remain in Silver. Only duration, distance, and speed define measurement eligibility; fares are not an eligibility condition. This pipeline uses `F.timestamp_diff`, available in PySpark 4.0+.
# MAGIC 
# MAGIC **Write behavior:** the final `CREATE OR REPLACE TABLE` creates or fully refreshes `workspace.default.nyc_taxi_silver_2025_01`. It does not append duplicates. Selected unchanged cells retain recorded outputs; edited cells must be rerun in Databricks.
# MAGIC 
# MAGIC ## Steps
# COMMAND ----------
from pyspark.sql import functions as F

raw_volume = "/Volumes/workspace/default/nyc_taxi_raw"
assert hasattr(F, "timestamp_diff"), "Use a Databricks Python environment with PySpark 4.0+."
# COMMAND ----------
# MAGIC %md
# MAGIC ### Load the raw January file
# COMMAND ----------
taxi_raw = spark.read.parquet(
    f"{raw_volume}/yellow_tripdata_2025-01.parquet"
)

taxi_raw.printSchema()
display(taxi_raw.limit(5))
# COMMAND ----------
# MAGIC %md
# MAGIC ### Inspect payment categories
# COMMAND ----------
display(
    taxi_raw
    .groupBy("payment_type")
    .count()
    .orderBy("payment_type")
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### Inspect rate codes
# COMMAND ----------
display(
    taxi_raw
    .groupBy("RatecodeID")
    .count()
    .orderBy("RatecodeID")
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### Inspect missing rate codes within payment category 0
# COMMAND ----------
display(
    taxi_raw
    .filter("payment_type = 0")
    .groupBy("RatecodeID")
    .count()
    .orderBy("RatecodeID")
)
# COMMAND ----------
# MAGIC %md
# MAGIC **Recorded observation:** 540,149 raw-file records have payment category 0 and a null `RatecodeID`. The TLC dictionary identifies category 0 as Flex Fare. Missing rate codes alone are not used to discard these records.
# COMMAND ----------
# MAGIC %md
# MAGIC ### Check raw row count and date range
# COMMAND ----------
from pyspark.sql import functions as F

display(
    taxi_raw.agg(
        F.count("*").alias("kayit_sayisi"),
        F.min("tpep_pickup_datetime").alias("ilk_baslangic"),
        F.max("tpep_pickup_datetime").alias("son_baslangic")
    )
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### Count records inside and outside January
# COMMAND ----------
baslangic = F.col("tpep_pickup_datetime")

display(
    taxi_raw
    .withColumn(
        "tarih_grubu",
        F.when(baslangic.isNull(), "Boş")
         .when(baslangic < "2025-01-01", "Ocak öncesi")
         .when(baslangic >= "2025-02-01", "Ocak sonrası")
         .otherwise("Ocak içi")
    )
    .groupBy("tarih_grubu")
    .count()
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### Select January pickup timestamps
# COMMAND ----------
taxi_jan = taxi_raw.filter(
    (F.col("tpep_pickup_datetime") >= "2025-01-01") &
    (F.col("tpep_pickup_datetime") < "2025-02-01")
)

print(taxi_jan.count())
# COMMAND ----------
# MAGIC %md
# MAGIC ### Calculate elapsed duration
# COMMAND ----------
taxi_sure = taxi_jan.withColumn(
    "sure_dakika",
    F.timestamp_diff(
        "SECOND",
        F.col("tpep_pickup_datetime"),
        F.col("tpep_dropoff_datetime")
    ) / 60.0
)

display(
    taxi_sure.select(
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "sure_dakika",
        "trip_distance"
    ).limit(5)
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### Review duration groups
# COMMAND ----------
sure = F.col("sure_dakika")

display(
    taxi_sure
    .withColumn(
        "sure_grubu",
        F.when(sure.isNull(), "Boş")
         .when(sure <= 0, "Sıfır veya negatif")
         .when(sure > 1200, "20 saatten uzun")
         .when(sure > 180, "3–20 saat")
         .otherwise("0–3 saat")
    )
    .groupBy("sure_grubu")
    .count()
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### Inspect the longest durations
# COMMAND ----------
display(
    taxi_sure
    .filter(F.col("sure_dakika") > 1200)
    .select(
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "sure_dakika",
        "trip_distance",
        "fare_amount",
        "payment_type"
    )
    .orderBy(F.col("sure_dakika").desc())
    .limit(10)
)
# COMMAND ----------
# MAGIC %md
# MAGIC **Recorded observation:** 935 January records exceed 20 hours and require investigation before duration analysis.
# COMMAND ----------
# MAGIC %md
# MAGIC ### Load taxi-zone reference data
# COMMAND ----------
zones = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv(f"{raw_volume}/taxi_zone_lookup.csv")
)

zones.printSchema()
display(zones.limit(5))
# COMMAND ----------
# MAGIC %md
# MAGIC ### Check lookup keys
# COMMAND ----------
zones.select(
    F.count("*").alias("toplam_satir"),
    F.countDistinct("LocationID").alias("benzersiz_location_id")
).display()
# COMMAND ----------
zone_stats = zones.agg(
    F.count("*").alias("rows"),
    F.countDistinct("LocationID").alias("unique_ids"),
    F.sum(F.col("LocationID").isNull().cast("int")).alias("null_ids")
).first()
assert zone_stats["rows"] == zone_stats["unique_ids"] and zone_stats["null_ids"] == 0,     "Taxi-zone lookup must contain one non-null row per LocationID."
# COMMAND ----------
# MAGIC %md
# MAGIC ### Enrich pickup location
# COMMAND ----------
pickup_zones = zones.select(
    F.col("LocationID").alias("PULocationID"),
    F.col("Borough").alias("pickup_borough"),
    F.col("Zone").alias("pickup_zone")
)

taxi_pickup = taxi_sure.join(
    pickup_zones,
    on="PULocationID",
    how="left"
)

display(
    taxi_pickup.select(
        "PULocationID", "pickup_borough", "pickup_zone", "sure_dakika"
    ).limit(10)
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### Enrich drop-off location
# COMMAND ----------
dropoff_zones = zones.select(
    F.col("LocationID").alias("DOLocationID"),
    F.col("Borough").alias("dropoff_borough"),
    F.col("Zone").alias("dropoff_zone")
)

taxi_bolgeler = taxi_pickup.join(
    dropoff_zones,
    on="DOLocationID",
    how="left"
)

display(
    taxi_bolgeler.select(
        "pickup_zone", "dropoff_zone", "sure_dakika"
    ).limit(10)
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### Reconcile join count and unmatched locations
# COMMAND ----------
taxi_bolgeler.select(
    F.count("*").alias("yolculuk_sayisi"),
    F.sum(F.col("pickup_zone").isNull().cast("int")).alias("binis_bolgesi_yok"),
    F.sum(F.col("dropoff_zone").isNull().cast("int")).alias("inis_bolgesi_yok")
).display()
# COMMAND ----------
assert taxi_bolgeler.count() == taxi_jan.count(),     "A zone join multiplied the January records; inspect lookup keys."
# COMMAND ----------
# MAGIC %md
# MAGIC ### Rank pickup zones
# COMMAND ----------
display(
    taxi_bolgeler
    .groupBy("pickup_borough", "pickup_zone")
    .count()
    .orderBy(F.desc("count"))
    .limit(10)
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### Rank pickup–drop-off pairs
# COMMAND ----------
display(
    taxi_bolgeler
    .groupBy("pickup_zone", "dropoff_zone")
    .count()
    .orderBy(F.desc("count"))
    .limit(10)
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### Inspect distance quality
# COMMAND ----------
taxi_bolgeler.select(
    F.count("*").alias("toplam"),
    F.sum(F.col("trip_distance").isNull().cast("int")).alias("mesafe_bos"),
    F.sum((F.col("trip_distance") <= 0).cast("int")).alias("mesafe_sifir_veya_negatif"),
    F.min("trip_distance").alias("en_kucuk_mesafe"),
    F.max("trip_distance").alias("en_buyuk_mesafe")
).display()
# COMMAND ----------
# MAGIC %md
# MAGIC ### Inspect the longest distances
# COMMAND ----------
display(
    taxi_bolgeler
    .select(
        "tpep_pickup_datetime", "tpep_dropoff_datetime",
        "pickup_zone", "dropoff_zone",
        "trip_distance", "sure_dakika", "total_amount"
    )
    .orderBy(F.desc("trip_distance"))
    .limit(10)
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### Count distance outliers
# COMMAND ----------
taxi_bolgeler.select(
    F.sum((F.col("trip_distance") > 100).cast("int")).alias("100_mil_ustu"),
    F.sum((F.col("trip_distance") > 1000).cast("int")).alias("1000_mil_ustu")
).display()
# COMMAND ----------
# MAGIC %md
# MAGIC ### Label distance quality
# COMMAND ----------
taxi_kalite = taxi_bolgeler.withColumn(
    "mesafe_durumu",
    F.when(F.col("trip_distance").isNull(), "Boş mesafe")
     .when(F.col("trip_distance") < 0, "Negatif mesafe")
     .when(F.col("trip_distance") == 0, "Sıfır mesafe")
     .when(F.col("trip_distance") > 1000, "Aşırı uç - incele")
     .when(F.col("trip_distance") > 100, "Uzun - incele")
     .otherwise("0-100 mil")
)

display(taxi_kalite.groupBy("mesafe_durumu").count())
# COMMAND ----------
# MAGIC %md
# MAGIC ### Label duration quality
# COMMAND ----------
taxi_kalite = taxi_kalite.withColumn(
    "sure_durumu",
    F.when(F.col("sure_dakika").isNull(), "Boş süre")
     .when(F.col("sure_dakika") <= 0, "Sıfır veya negatif")
     .when(F.col("sure_dakika") > 1200, "20 saatten uzun - incele")
     .when(F.col("sure_dakika") > 180, "3-20 saat - incele")
     .otherwise("0-3 saat")
)

display(taxi_kalite.groupBy("sure_durumu").count())
# COMMAND ----------
# MAGIC %md
# MAGIC ### Cross-tabulate distance and duration labels
# COMMAND ----------
display(
    taxi_kalite
    .groupBy("sure_durumu")
    .pivot("mesafe_durumu", [
        "0-100 mil",
        "Boş mesafe",
        "Negatif mesafe",
        "Sıfır mesafe",
        "Uzun - incele",
        "Aşırı uç - incele"
    ])
    .count()
    .fillna(0)
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### Review zero-distance records by payment category
# COMMAND ----------
display(
    taxi_kalite
    .filter(F.col("trip_distance") == 0)
    .groupBy("payment_type")
    .agg(
        F.count("*").alias("kayit"),
        F.sum((F.col("total_amount") > 0).cast("int")).alias("pozitif_tutarli")
    )
    .orderBy(F.desc("kayit"))
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### Select distance and duration candidates
# COMMAND ----------
taxi_olcum = taxi_kalite.filter(
    (F.col("trip_distance") > 0) &
    (F.col("trip_distance") <= 100) &
    (F.col("sure_dakika") > 0) &
    (F.col("sure_dakika") <= 180)
)

print("Ölçüm analizine aday kayıt:", taxi_olcum.count())
# COMMAND ----------
# MAGIC %md
# MAGIC ### Calculate speed and inspect outliers
# COMMAND ----------
taxi_olcum = taxi_olcum.withColumn(
    "ortalama_hiz_mph",
    F.col("trip_distance") * 60 / F.col("sure_dakika")
)

display(
    taxi_olcum.select(
        F.sum((F.col("ortalama_hiz_mph") > 80).cast("int")).alias("80_mph_ustu"),
        F.max("ortalama_hiz_mph").alias("en_yuksek_hiz")
    )
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### Label speed candidates
# COMMAND ----------
taxi_olcum = taxi_olcum.withColumn(
    "hiz_durumu",
    F.when(
        F.col("ortalama_hiz_mph") > 80,
        "Yüksek hız - incele"
    ).otherwise("80 mph ve altı")
)

display(taxi_olcum.groupBy("hiz_durumu").count())
# COMMAND ----------
# MAGIC %md
# MAGIC ### Inspect implausible speeds
# COMMAND ----------
display(
    taxi_olcum
    .filter(F.col("ortalama_hiz_mph") > 80)
    .select(
        "pickup_zone",
        "dropoff_zone",
        "trip_distance",
        "sure_dakika",
        "ortalama_hiz_mph",
        "total_amount"
    )
    .orderBy(F.desc("ortalama_hiz_mph"))
    .limit(10)
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### Select candidates at or below 80 mph
# COMMAND ----------
taxi_olcum_temiz = taxi_olcum.filter(
    F.col("ortalama_hiz_mph") <= 80
)

print("Ölçüm analizine seçilen kayıt:", taxi_olcum_temiz.count())
# COMMAND ----------
# MAGIC %md
# MAGIC ### Build the Silver eligibility flag
# COMMAND ----------
taxi_silver = (
    taxi_kalite
    .withColumn(
        "ortalama_hiz_mph",
        F.when(
            F.col("sure_dakika") > 0,
            F.col("trip_distance") * 60 / F.col("sure_dakika")
        )
    )
    .withColumn(
        "olcum_analizine_uygun",
        F.coalesce(
            (F.col("trip_distance") > 0) &
            (F.col("trip_distance") <= 100) &
            (F.col("sure_dakika") > 0) &
            (F.col("sure_dakika") <= 180) &
            (F.col("ortalama_hiz_mph") <= 80),
            F.lit(False)
        )
    )
)

display(
    taxi_silver
    .groupBy("olcum_analizine_uygun")
    .count()
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### Persist the Silver Delta table
# COMMAND ----------
taxi_silver.createOrReplaceTempView("taxi_silver_hazir")

spark.sql("""
    CREATE OR REPLACE TABLE workspace.default.nyc_taxi_silver_2025_01
    USING DELTA
    AS SELECT * FROM taxi_silver_hazir
""")
# COMMAND ----------
# MAGIC %md
# MAGIC ### Review persisted eligibility counts
# COMMAND ----------
display(
    spark.table("workspace.default.nyc_taxi_silver_2025_01")
    .groupBy("olcum_analizine_uygun")
    .count()
)
# COMMAND ----------
# MAGIC %md
# MAGIC ## Checks and recorded baseline
# MAGIC | Measure | Recorded value |
# MAGIC |---|---:|
# MAGIC | Raw-file records | 3,475,226 |
# MAGIC | Outside January pickup window | 22 |
# MAGIC | January / Silver records | 3,475,204 |
# MAGIC | Distance and duration candidates | 3,381,449 |
# MAGIC | Candidate speeds above 80 mph | 857 |
# MAGIC | Measurement-eligible records | 3,380,592 |
# MAGIC | Measurement-ineligible records retained in Silver | 94,612 |
# MAGIC 
# MAGIC The largest candidate speed is approximately 67,608 mph: 18.78 miles in one second. This is an implausible derived observation, not an actual measured vehicle speed.
# MAGIC 
# MAGIC Null and negative distance labels are explicit in the packaged version. The final eligibility predicate remains the original project rule: distance > 0 and <= 100 miles, duration > 0 and <= 180 minutes, speed <= 80 mph, and null predicates mapped to false.
# MAGIC 
# MAGIC ## Next steps
# MAGIC Run notebook 03 for Silver analysis and notebook 04 to create the Gold day/hour table.
