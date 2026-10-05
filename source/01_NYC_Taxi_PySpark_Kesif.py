# Databricks notebook source
# MAGIC %md
# MAGIC # NYC Taxi | PySpark exploration
# MAGIC 
# MAGIC ## Goal
# MAGIC Practice PySpark on `samples.nyctaxi.trips`: inspect the schema, calculate duration, identify quality issues, and group records by pickup ZIP code.
# MAGIC 
# MAGIC ## Setup
# MAGIC This is an **optional introductory notebook**, independent of the January 2025 pipeline. The recorded sample contains 21,932 records from 2016. Its results and eligibility rules must not be combined with the January 2025 results in notebooks 02–05.
# MAGIC 
# MAGIC Run in Databricks with Python as the default notebook language. Selected table outputs below are recorded outputs from the original export, not a fresh execution of this packaged notebook.
# MAGIC 
# MAGIC ## Steps
# COMMAND ----------
# MAGIC %md
# MAGIC ### Load the Databricks sample table
# COMMAND ----------
taxi = spark.read.table("samples.nyctaxi.trips")
display(taxi.limit(10))
# COMMAND ----------
# MAGIC %md
# MAGIC ### Inspect the schema
# COMMAND ----------
taxi.printSchema()
# COMMAND ----------
# MAGIC %md
# MAGIC ### Calculate duration in minutes
# COMMAND ----------
from pyspark.sql.functions import  col
 
taxi_sure = taxi.withColumn (
    "sure_dakika",
    (col("tpep_dropoff_datetime").cast("long")
     - col("tpep_pickup_datetime").cast("long")) / 60
) 
display(taxi_sure.select(
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "sure_dakika"
).limit(10))
# COMMAND ----------
# MAGIC %md
# MAGIC ### Inspect suspicious durations
# COMMAND ----------
display(
    taxi_sure
    .filter(
        col("sure_dakika").isNull()
        | (col("sure_dakika") <= 0)
        | (col("sure_dakika") > 180)
    )
    .select(
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "trip_distance",
        "sure_dakika"
    )
    .limit(10)
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### Summarize duration quality
# COMMAND ----------
from pyspark.sql import functions as F

display(
    taxi_sure.agg(
        F.count("*").alias("toplam_kayit"),
        F.sum(F.when(F.col("sure_dakika").isNull(), 1).otherwise(0)).alias("bos_sure"),
        F.sum(F.when(F.col("sure_dakika") <= 0, 1).otherwise(0)).alias("sifir_veya_negatif"),
        F.sum(F.when(
            (F.col("sure_dakika") > 180) & (F.col("sure_dakika") <= 1200), 1
        ).otherwise(0)).alias("uc_ile_yirmi_saat_arasi"),
        F.sum(F.when(F.col("sure_dakika") > 1200, 1).otherwise(0)).alias("yirmi_saatten_uzun")
    )
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### Inspect non-positive and long durations
# COMMAND ----------
display(
    taxi_sure
    .filter(
        (F.col("sure_dakika") <= 0)
        | (
            (F.col("sure_dakika") > 180)
            & (F.col("sure_dakika") <= 1200)
        )
    )
    .select(
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "trip_distance",
        "fare_amount",
        "sure_dakika"
    )
    .orderBy("sure_dakika")
    .limit(20)
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### Label duration suitability
# COMMAND ----------
taxi_kalite = taxi_sure.withColumn(
    "sure_durumu",
    F.when(F.col("sure_dakika").isNull(), "bos")
     .when(F.col("sure_dakika") <= 0, "sifir_veya_negatif")
     .when(F.col("sure_dakika") > 180, "uc_saatten_uzun")
     .otherwise("uygun")
)

display(
    taxi_kalite
    .groupBy("sure_durumu")
    .count()
    .orderBy("sure_durumu")
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### Check distance and fare among duration candidates
# COMMAND ----------
taxi_sure_uygun = taxi_kalite.filter(F.col("sure_durumu") == "uygun")

display(
    taxi_sure_uygun.agg(
        F.count("*").alias("sure_acisindan_uygun"),
        F.sum(F.when(
            F.col("trip_distance").isNull() | (F.col("trip_distance") <= 0),
            1
        ).otherwise(0)).alias("bos_veya_sifir_mesafe"),
        F.sum(F.when(
            F.col("fare_amount").isNull() | (F.col("fare_amount") < 0),
            1
        ).otherwise(0)).alias("bos_veya_negatif_ucret")
    )
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### Compare overlapping issues
# COMMAND ----------
taxi_kontrol = (
    taxi_sure_uygun
    .withColumn(
        "mesafe_sorunu",
        F.col("trip_distance").isNull() | (F.col("trip_distance") <= 0)
    )
    .withColumn(
        "ucret_sorunu",
        F.col("fare_amount").isNull() | (F.col("fare_amount") < 0)
    )
)

display(
    taxi_kontrol
    .groupBy("mesafe_sorunu", "ucret_sorunu")
    .count()
    .orderBy("mesafe_sorunu", "ucret_sorunu")
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### Summarize the introductory analysis subset
# COMMAND ----------
taxi_analiz = taxi_kontrol.filter(
    (~F.col("mesafe_sorunu")) & (~F.col("ucret_sorunu"))
)

display(
    taxi_analiz.agg(
        F.count("*").alias("analize_uygun_kayit"),
        F.round(F.avg("sure_dakika"), 2).alias("ortalama_sure_dakika"),
        F.round(F.avg("trip_distance"), 2).alias("ortalama_mesafe"),
        F.round(F.avg("fare_amount"), 2).alias("ortalama_ucret")
    )
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### Compare pickup ZIP codes
# COMMAND ----------
display(
    taxi_analiz
    .groupBy("pickup_zip")
    .agg(
        F.count("*").alias("yolculuk_sayisi"),
        F.round(F.avg("sure_dakika"), 2).alias("ortalama_sure"),
        F.round(F.avg("fare_amount"), 2).alias("ortalama_ucret")
    )
    .orderBy(F.desc("yolculuk_sayisi"))
    .limit(10)
)
# COMMAND ----------
# MAGIC %md
# MAGIC ## Checks and takeaways
# MAGIC The recorded sample analysis selected 21,818 records after duration, distance, and fare checks. This is a teaching subset of the sample data, **not** the January 2025 measurement population.
# MAGIC 
# MAGIC ## Next steps
# MAGIC Use notebook 02 to start the independent pipeline from the TLC January 2025 Parquet and taxi-zone CSV files. Notebook 01 creates no persistent project table.
