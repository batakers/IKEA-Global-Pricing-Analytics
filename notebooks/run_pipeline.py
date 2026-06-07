from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import assert_pipeline_healthy, persist_pipeline_manifest  # noqa: E402


def _run_step(name: str, script: str) -> dict[str, object]:
    command = [sys.executable, str(PROJECT_ROOT / script)]
    started = time.perf_counter()

    print(f"\nRunning step: {name}")
    print(f"Command: {' '.join(command)}")
    result = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    duration_seconds = round(time.perf_counter() - started, 3)

    step = {
        "name": name,
        "command": f"python {script}",
        "duration_seconds": duration_seconds,
        "return_code": result.returncode,
        "status": "pass" if result.returncode == 0 else "fail",
    }

    if result.returncode != 0:
        raise RuntimeError(f"Pipeline step failed: {name} ({script})")

    return step


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the IKEA pricing analytics pipeline.")
    parser.add_argument(
        "--include-raw-prep",
        action="store_true",
        help="Run 01_data_preparation.py from local raw catalog input before downstream steps.",
    )
    parser.add_argument(
        "--refresh-preview",
        action="store_true",
        help="Regenerate README dashboard preview images after data outputs are refreshed.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    steps: list[dict[str, object]] = []

    if args.include_raw_prep:
        steps.append(_run_step("data_preparation", "notebooks/01_data_preparation.py"))
    else:
        print("Skipping data_preparation: using committed data/processed_catalog.csv sample.")
        steps.append(
            {
                "name": "data_preparation",
                "command": "python notebooks/01_data_preparation.py",
                "duration_seconds": 0.0,
                "return_code": None,
                "status": "skipped",
                "reason": "Raw IKEA catalog is a local ignored input; default run uses committed processed sample.",
            }
        )

    steps.append(_run_step("country_aggregation", "notebooks/02_country_aggregation.py"))
    steps.append(_run_step("market_clustering", "notebooks/05_market_clustering.py"))
    steps.append(_run_step("cluster_validation", "notebooks/07_cluster_validation.py"))

    if args.refresh_preview:
        steps.append(_run_step("dashboard_preview_generation", "notebooks/generate_readme_images.py"))

    manifest = persist_pipeline_manifest(steps=steps)
    assert_pipeline_healthy(manifest)

    print("\nPipeline completed.")
    print(f"Manifest status: {manifest['status']}")
    print("Manifest path: data/pipeline_manifest.json")
    print(f"Checks passed: {sum(1 for check in manifest['checks'] if check['status'] == 'pass')}")


if __name__ == "__main__":
    main()
