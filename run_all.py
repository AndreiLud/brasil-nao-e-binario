"""Run the whole pipeline: download -> clean -> crosswalk -> model -> validation ->
questions (SQL) -> site data -> facts -> notebook -> rendered site and READMEs.

Usage:
    python run_all.py              # everything (downloads only what is missing)
    python run_all.py --skip-download
    python run_all.py --skip-notebook
"""
from __future__ import annotations

import argparse
import sys
import time

from src import config as C
from src import crosswalk, download, export, facts, pipeline_db, validate
from src.quality import QualityLog

QUESTION_SQL = ["q1_national.sql", "q2_municipal.sql", "q3_mixture.sql", "q4_rise_2018.sql",
                "q5_recovery_2022.sql", "q6_turnaround_2026.sql", "q7_context.sql"]


def step(name):
    print(f"\n== {name}")
    return time.time()


def main(skip_download=False, skip_notebook=False):
    t0 = time.time()
    if not skip_download:
        step("Download raw data")
        download.main()
    log = QualityLog()
    step("Crosswalk TSE <-> IBGE")
    crosswalk.build(log)

    step("Staging and model (DuckDB)")
    con = pipeline_db.connect(fresh=True)
    pipeline_db.run_sql(con, "00_staging.sql")
    pipeline_db.load_reference(con)
    pipeline_db.run_sql(con, "01_model.sql")
    from src import checks
    checks.run(con, log)

    step("Validation against official TSE totals")
    validate.run(con, log)

    step("Questions (one SQL file per question)")
    for f in QUESTION_SQL:
        pipeline_db.run_sql(con, f)
        print(f"  ran sql/{f}")
    export.processed_tables(con)

    step("Site data (mesh, results, dots, chapter aggregates)")
    export.site_data(con, log)

    step("Facts")
    facts.build(con)

    log.flush()
    if log.failures:
        print("\nUnexplained quality failures:")
        for f in log.failures:
            print("  -", f["section"], "|", f["name"], "|", f["observed"], "expected", f["expected"])
        sys.exit(1)

    step("Render site text and READMEs from templates")
    from src import render
    render.main()

    if not skip_notebook:
        step("Execute EDA notebook")
        from src import notebook
        notebook.run()
    print(f"\nDone in {time.time() - t0:,.0f} s.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skip-download", action="store_true")
    ap.add_argument("--skip-notebook", action="store_true")
    a = ap.parse_args()
    main(a.skip_download, a.skip_notebook)
