"""
run_pipeline.py
---------------
Runs the entire data pipeline in the correct dependency order, so that
downstream stages never see stale data from an earlier partial run.

This exists because of a real bug class found during Sprint 3 Day 18/20:
loader.py rebuilds financial_ratios from the RAW source Excel file
(wiping out every column we compute ourselves), so any script that reads
from financial_ratios/peer_percentiles after a schema change but before
the full chain re-runs will silently see nulls/stale values instead of
an error - which is much harder to notice than a crash.

Run with: python run_pipeline.py
"""
import subprocess
import sys

STEPS = [
    ("Load all 12 source files into SQLite", ["python", "src/etl/loader.py"]),
    ("Run 16 DQ rules validator", ["python", "src/etl/validator.py"]),
    ("Compute and populate financial_ratios", ["python", "src/analytics/populate_ratios.py"]),
    ("Compute peer percentile rankings", ["python", "src/analytics/peer.py"]),
    ("Generate radar charts", ["python", "src/analytics/radar.py"]),
    ("Generate capital_allocation.csv", ["python", "src/analytics/generate_capital_allocation.py"]),
    ("Generate ratio_edge_cases.log", ["python", "src/analytics/edge_case_log.py"]),
    ("Generate screener_output.xlsx", ["python", "src/screener/export_screener.py"]),
    ("Generate peer_comparison.xlsx", ["python", "src/analytics/export_peer_comparison.py"]),
]


def main():
    for step_name, command in STEPS:
        print(f"\n{'=' * 60}")
        print(f"STEP: {step_name}")
        print(f"{'=' * 60}")
        result = subprocess.run(command)
        if result.returncode != 0:
            print(f"\nFAILED at step: {step_name}")
            print("Stopping pipeline - fix the error above before continuing.")
            sys.exit(1)

    print(f"\n{'=' * 60}")
    print("PIPELINE COMPLETE - all steps ran successfully in order")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()