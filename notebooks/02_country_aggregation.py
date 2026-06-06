from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.aggregation import (
    BENCHMARK_OUTPUT,
    COUNTRY_OUTPUT,
    create_country_metrics,
    create_product_benchmark,
    load_clean_data,
)


def main() -> None:
    clean_df = load_clean_data()
    metrics_df = create_country_metrics(clean_df)
    benchmark_df = create_product_benchmark(clean_df)

    COUNTRY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    metrics_df.to_csv(COUNTRY_OUTPUT, index=False)
    benchmark_df.to_csv(BENCHMARK_OUTPUT, index=False)

    print(f"Saved country metrics to: {COUNTRY_OUTPUT}")
    print(f"Saved product benchmark table to: {BENCHMARK_OUTPUT}")
    print(f"Countries aggregated: {metrics_df['country'].nunique():,}")


if __name__ == "__main__":
    main()
