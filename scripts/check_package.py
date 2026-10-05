"""Validate the handoff package without executing Databricks or reading raw data."""
from pathlib import Path
import ast
import csv
import json
import re
import sys
import nbformat
import sqlglot
from sqlglot import exp

ROOT = Path(__file__).resolve().parents[1]
errors = []
counts = {"notebooks": 0, "python_cells": 0, "sql_statements_parsed": 0,
          "runtime_commands_review_required": 0, "local_links": 0}

def check(condition, message):
    if not condition:
        errors.append(message)


def parse_sql(source, label):
    # sqlglot does not parse these two Databricks-specific runtime commands.
    # Check their canonical structure separately and keep the execution gap visible.
    runtime_pattern = re.compile(
        r"(?im)^\s*(?:DESCRIBE\s+DETAIL\s+[A-Za-z_][\w.]*"
        r"|RESTORE\s+TABLE\s+[A-Za-z_][\w.]*\s+TO\s+VERSION\s+AS\s+OF\s+\d+)\s*;"
    )
    source, runtime_count = runtime_pattern.subn("", source)
    counts["runtime_commands_review_required"] += runtime_count
    try:
        for statement in sqlglot.parse(source, read="databricks"):
            if statement is None:
                continue
            if isinstance(statement, exp.Command):
                # E.g. RESTORE: retained as a runtime command, not a parsed query.
                counts["runtime_commands_review_required"] += 1
            else:
                counts["sql_statements_parsed"] += 1
    except Exception as exc:
        errors.append(f"{label}: SQL parsing failed: {exc}")


def source_export(notebook):
    sql_only = all(cell.source.lstrip().startswith("%sql")
                   for cell in notebook.cells if cell.cell_type == "code")
    comment = "--" if sql_only else "#"
    parts = [f"{comment} Databricks notebook source"]
    for index, cell in enumerate(notebook.cells):
        if index:
            parts.append(f"{comment} COMMAND ----------")
        if cell.cell_type == "markdown":
            parts.append(f"{comment} MAGIC %md")
            parts.extend(f"{comment} MAGIC {line}" for line in cell.source.splitlines())
        elif sql_only:
            parts.append(cell.source.removeprefix("%sql").lstrip("\n"))
        elif cell.source.startswith("%"):
            parts.extend(f"{comment} MAGIC {line}" for line in cell.source.splitlines())
        else:
            parts.append(cell.source)
    return "\n".join(parts) + "\n", ".sql" if sql_only else ".py"


notebook_paths = sorted((ROOT / "notebooks").glob("*.ipynb"))
check(len(notebook_paths) == 5, "Expected five curated notebooks")
for path in notebook_paths:
    try:
        notebook = nbformat.read(path, as_version=4)
        nbformat.validate(notebook)
        counts["notebooks"] += 1
        for index, cell in enumerate(notebook.cells):
            if cell.cell_type != "code":
                continue
            source = cell.source.lstrip()
            if source.startswith("%sql"):
                parse_sql(source.split("\n", 1)[1], f"{path.name}, cell {index}")
            else:
                tree = ast.parse(source, filename=f"{path.name}:{index}")
                counts["python_cells"] += 1
                for node in ast.walk(tree):
                    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                            and node.func.attr == "sql" and node.args
                            and isinstance(node.args[0], ast.Constant)
                            and isinstance(node.args[0].value, str)):
                        parse_sql(node.args[0].value, f"{path.name}, embedded SQL {index}")
            for output in cell.get("outputs", []):
                check(output.output_type != "error", f"{path.name}: error output retained")
                check(not output.get("metadata", {}), f"{path.name}: output metadata retained")
        expected, extension = source_export(notebook)
        export = ROOT / "source" / (path.stem + extension)
        check(export.is_file() and export.read_text() == expected,
              f"{path.name}: source export differs from notebook")
    except Exception as exc:
        errors.append(f"{path.name}: {exc}")

for path in (ROOT / "source").glob("*.py"):
    try:
        ast.parse(path.read_text(), filename=path.name)
    except SyntaxError as exc:
        errors.append(f"{path.name}: {exc}")
for path in (ROOT / "sql").glob("*.sql"):
    parse_sql(path.read_text(), path.name)

# Verify retained aggregate evidence without presenting it as a fresh raw-data run.
metrics = json.loads((ROOT / "results/observed_metrics.json").read_text())
check(metrics["eligible_records"] + metrics["ineligible_records"] == metrics["january_records"],
      "Eligibility totals do not reconcile")
check(metrics["raw_records"] - metrics["outside_january_records"] == metrics["january_records"],
      "Raw/January window totals do not reconcile")
check(metrics["candidate_records"] - metrics["candidate_speed_above_80_mph"] == metrics["eligible_records"],
      "Candidate speed exclusion does not reconcile")
with (ROOT / "results/hourly_pickup_counts.csv").open(newline="") as handle:
    hourly = list(csv.DictReader(handle))
check([int(row["binis_saati"]) for row in hourly] == list(range(24)), "Hourly extract lacks the 0–23 grid")
check(sum(int(row["yolculuk_kaydi_sayisi"]) for row in hourly) == metrics["january_records"],
      "Hourly extract does not reconcile to January count")
peak = max(hourly, key=lambda row: int(row["yolculuk_kaydi_sayisi"]))
low = min(hourly, key=lambda row: int(row["yolculuk_kaydi_sayisi"]))
check(int(peak["binis_saati"]) == metrics["hourly_peak"]["hour"] and
      int(peak["yolculuk_kaydi_sayisi"]) == metrics["hourly_peak"]["records"], "Peak hour differs")
check(int(low["binis_saati"]) == metrics["hourly_low"]["hour"] and
      int(low["yolculuk_kaydi_sayisi"]) == metrics["hourly_low"]["records"], "Lowest hour differs")
with (ROOT / "results/gold_first_day_sample.csv").open(newline="") as handle:
    sample = list(csv.DictReader(handle))
check(len(sample) == 24 and all(row["binis_tarihi"] == "2025-01-01" for row in sample),
      "January 1 sample has a different scope")
check(sum(int(row["yolculuk_kaydi_sayisi"]) for row in sample) == metrics["january_1_total_records"],
      "January 1 total differs")
check(sum(int(row["olcume_uygun_kayit_sayisi"]) for row in sample) == metrics["january_1_eligible_records"],
      "January 1 eligible total differs")

for path in [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md")), ROOT / "results/README.md"]:
    for target in re.findall(r"!?\[[^\]]*\]\(([^\s)]+)\)", path.read_text()):
        if target.startswith(("https://", "http://", "#", "mailto:")):
            continue
        destination = (path.parent / target.split("#", 1)[0]).resolve()
        check(destination.exists(), f"{path.relative_to(ROOT)}: broken link {target}")
        counts["local_links"] += 1

# Only scan textual public artifacts, not binary assets.
for path in ROOT.rglob("*"):
    if path.is_file() and path.suffix in {".md", ".py", ".sql", ".ipynb", ".json", ".csv", ".txt"}:
        text = path.read_text()
        email_pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
        check(not re.search(email_pattern, text), f"{path.relative_to(ROOT)}: email address retained")


if errors:
    print("Package check FAILED:")
    print("\n".join(f"- {error}" for error in errors))
    sys.exit(1)
print("Package check PASSED (static checks and recorded-evidence reconciliation only).")
print(json.dumps(counts, indent=2))
print("Databricks execution: NOT RUN here. Follow docs/VALIDATION.md in the target workspace.")
