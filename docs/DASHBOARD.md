# Reconstruct the Databricks dashboard

The dashboard in `dashboard/nyc_taxi_january_2025.pdf` is a static author-supplied export. The repository does not include a native dashboard layout JSON. Rebuild its interactive view using the following dataset and bindings.

## Dataset

Run notebook 04, then use `sql/dashboard_dataset.sql` as the dashboard dataset query. SQL editor queries must not include the notebook-only `%sql` prefix. Suggested dataset name: **Gün ve Saat Özeti**.

## Widget bindings

| Widget | Type | Binding |
|---|---|---|
| Tarih Aralığı | Date range filter | `binis_tarihi` across the dataset |
| Toplam Yolculuk Kaydı | Counter | SUM(`yolculuk_kaydi_sayisi`) |
| Ölçüme Uygun Kayıt | Counter | SUM(`olcume_uygun_kayit_sayisi`) |
| Günlük Yolculuk Başlangıçları | Line | X=`binis_tarihi`, Y=SUM(`yolculuk_kaydi_sayisi`), date ascending |
| Saate Göre Yolculuk Başlangıçları | Bar | X=`binis_saati`, Y=SUM(`yolculuk_kaydi_sayisi`), hour ascending |

Arrange the date filter above the two counters, and place the daily and hourly charts beneath them. Display counters with zero decimal places, thousands separators and no abbreviation. Use numeric hours 0–23 so sorting remains chronological.

## Check the selected population

With the full January range selected and chart selections cleared:

- Total counter: **3,475,204**.
- Eligible counter: **3,380,592**.

For January 1 only:

- Total counter: **90,188**.
- Eligible counter: **88,517**.

A selected chart point can filter other widgets. Date filters and chart selections intersect; clear selections before interpreting a supposedly full-month view. The eligible counter is not the population of the volume charts, which use all January records.

The hourly chart aggregates all selected dates at each hour. Its recorded full-month maximum is hour 18, 267,951 records; minimum is hour 4, 20,033.

## Publish and export

When the reconstructed layout is ready, use the dashboard's Publish action under the access settings appropriate to your workspace. The original dashboard was published in the author's workspace; this repository does not create a public link or grant access to that workspace.

The supplied PDF has blank date-control fields and is static. Its displayed totals and chart span correspond to the recorded January analysis; blank controls must not be read as an interactive selection state. The PNG preview is rendered from that PDF without recreating or altering the plots.
