# Data quality rules

## Population and grain

One source row is treated as one **trip record**. The project does not identify unique people, deduplicate repeated trip attributes, or validate accounting cancellations/refunds. Count measures use all records with pickup time >= 2025-01-01 and < 2025-02-01. Raw records outside this window are omitted from Silver, rather than silently attributed to January.

The recorded raw file contains 21 pickups before January and one after it, leaving 3,475,204 January records. All these January records remain in Silver.

## Enrichment and derived fields

- Duration in minutes: whole-second difference from pickup to drop-off, divided by 60.0.
- Speed in mph: trip distance * 60 / positive duration; null otherwise.
- Pickup and drop-off enrichment: separate left joins to a zone lookup with unique, non-null LocationID keys.
- Recorded lookup: 265 keys; joined January row count unchanged; zero null pickup/drop-off zone names. Labels such as `Unknown` and `N/A` can still occur and are not equivalent to missing join matches.

The packaged notebook adds lookup uniqueness and row-count assertions to prevent join multiplication.

## Eligibility predicate

```sql
COALESCE(
    trip_distance > 0
    AND trip_distance <= 100
    AND sure_dakika > 0
    AND sure_dakika <= 180
    AND ortalama_hiz_mph <= 80,
    FALSE
)
```

| Rule | Meaning |
|---|---|
| Positive distance | Excludes zero, negative, and null distances from measurement means |
| Distance <= 100 miles | Project scope for measurement analysis |
| Positive duration <= 180 minutes | Includes short positive trips; there is no three-minute minimum |
| Speed <= 80 mph | Review threshold for implausible distance/time combinations |
| Null predicate -> false | Eligibility is a defined boolean, not an unknown value |

The thresholds are project heuristics, not proof that every included record is physically accurate. A record below a threshold can still contain an error. Fare values and RatecodeID missingness are deliberately separate from this measurement predicate.

## Recorded observations

| Observation | Records |
|---|---:|
| Zero distance | 90,893 |
| Distance above 100 miles | 162 |
| Distance above 1,000 miles (subset of the previous group) | 116 |
| Non-positive duration | 2,051 |
| Duration > 180 and <= 1,200 minutes | 442 |
| Duration > 1,200 minutes | 935 |
| Positive-distance / duration candidates | 3,381,449 |
| Candidate speed > 80 mph | 857 |
| Eligible | 3,380,592 |
| Ineligible but retained in Silver | 94,612 |

Issue counts overlap; do not sum them as independent exclusion categories. The speed count applies only to the distance/duration candidate population, not all January records. The maximum 67,608 mph derives from 18.78 miles in one second and is treated as an implausible record.

## Gold and dashboard interpretation

- `yolculuk_kaydi_sayisi`: all January records per pickup date/hour.
- `olcume_uygun_kayit_sayisi`: eligible January records in the same group.
- Measurement means: eligible records only; ineligible records do not contribute.
- Counter and date/hour charts: sums of the relevant count columns.
- The hourly chart pools every selected date at each pickup hour; it is not an average daily volume or an individual trip's elapsed time.
- Overall means require eligible-count weighting. Never average hourly means without their weights.

See the SQL checks and [verification notes](VALIDATION.md) for reconciliation and execution limits.
