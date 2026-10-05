-- Databricks dashboard dataset: all January date/hour groups.
-- SQL editor: do not prepend the notebook-only %sql magic.
SELECT
    binis_tarihi,
    binis_saati,
    yolculuk_kaydi_sayisi,
    olcume_uygun_kayit_sayisi,
    ortalama_mesafe_mil,
    ortalama_sure_dakika
FROM workspace.default.nyc_taxi_gold_gun_saat_2025_01;
