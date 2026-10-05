# Changes made for the repository handoff

The supplied files were teaching notebooks built incrementally. The curated package preserves the analysis scope while making roles and reruns clearer.

| Change | Reason |
|---|---|
| Add goals, setup, section labels, baseline notes, and next-step descriptions | Make each notebook understandable without the chat |
| Keep notebook 01 explicitly optional and independent | Separate the 2016 Databricks sample from the external January 2025 pipeline |
| Remove Gold creation and duplicate Gold checks from notebook 03 | Notebook 04 becomes the only owner of Gold creation |
| Remove the duplicate borough query at the end of notebook 02 | The same read-only analysis remains in notebook 03 |
| Use `CREATE OR REPLACE TABLE` for Silver and Gold | Avoid the recorded TABLE_OR_VIEW_ALREADY_EXISTS errors; refresh the fixed-month snapshots on reruns |
| Use `CREATE TABLE IF NOT EXISTS` for the demo table | Retain the first version used by the Time Travel exercise |
| Add explicit null/negative distance labels | Avoid labeling missing or negative distances as 0–100 miles |
| Use explicit candidate predicates | Match the final positive-distance/positive-duration rules rather than relying solely on label strings |
| Assert zone key uniqueness and unchanged joined row count | Guard against join multiplication |
| Bound one sample inspection to 20 rows | Keep output manageable |
| Separate the Gold preview from the totals query | Avoid hidden result selection in a multi-statement cell |
| Add Gold/Silver reconciliation SQL | Provide a repeatable post-run acceptance check |
| Strip session/account metadata, history/detail outputs, and stale errors | Keep the public notebooks portable and focused on the analysis |
| Keep outputs only for unchanged computations (including the identical extracted preview query) | Preserve supplied evidence without pretending changed code was rerun |

The final measurement eligibility predicate and its >0 duration threshold are unchanged. No fare-based filtering, three-minute threshold, deduplication, streaming, automated Jobs, or incremental ingestion was added. No change was applied to the author's live Databricks workspace: these are repository copies only.
