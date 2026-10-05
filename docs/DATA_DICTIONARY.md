# Project data dictionary

## Source fields used

| Column | Meaning / unit |
|---|---|
| `tpep_pickup_datetime` | Pickup timestamp; determines January population and grouping |
| `tpep_dropoff_datetime` | Drop-off timestamp; used with pickup for duration |
| `trip_distance` | Reported distance in miles |
| `PULocationID` / `DOLocationID` | Pickup/drop-off TLC zone keys |
| `payment_type` | Payment category; inspected, not an eligibility condition |
| `RatecodeID` | Rate category; inspected, nulls are retained |
| `fare_amount` / `total_amount` | Source monetary fields inspected in exploration; not used for final measurement eligibility |

See the official TLC dictionary for the complete raw schema and payment definitions. Notebook 01's ZIP fields belong to the separate sample schema.

## Silver additions

| Column | Definition |
|---|---|
| `sure_dakika` | Elapsed whole seconds / 60.0 |
| `pickup_borough` / `pickup_zone` | Left-joined pickup location labels |
| `dropoff_borough` / `dropoff_zone` | Left-joined drop-off location labels |
| `mesafe_durumu` | Distance label, including explicit null, negative, zero, >0–100, >100–1000, and >1000 mile groups |
| `sure_durumu` | Duration label for null, non-positive, <=180, >180–1200, >1200 minutes |
| `ortalama_hiz_mph` | Distance * 60 / positive duration; null otherwise |
| `olcum_analizine_uygun` | Boolean eligibility defined in DATA_QUALITY.md |

`hiz_durumu` is a temporary candidate-analysis label; it is not a persisted Silver addition. Original raw columns are preserved in Silver.

## Gold schema and grain

One row per `(binis_tarihi, binis_saati)`, derived from pickup time.

| Column | Meaning | Rollup |
|---|---|---|
| `binis_tarihi` | Pickup date | Group/filter |
| `binis_saati` | Pickup hour, 0–23 | Group/filter |
| `yolculuk_kaydi_sayisi` | Count of all January records in the date/hour group | Sum |
| `olcume_uygun_kayit_sayisi` | Eligible record count in the same group | Sum |
| `ortalama_mesafe_mil` | Eligible-only mean distance in miles | Weight by eligible count for non-null means |
| `ortalama_sure_dakika` | Eligible-only mean duration in minutes | Weight by eligible count for non-null means |

The original table has 744 groups. This is an observed complete 31×24 grid, not a generated calendar spine. Future inputs lacking an hour would require a calendar join to display an explicit zero; this fixed-month pipeline does not zero-fill missing groups.
