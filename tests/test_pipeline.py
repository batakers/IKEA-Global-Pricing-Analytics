from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.aggregation import (  # noqa: E402
    BENCHMARK_OUTPUT,
    COUNTRY_OUTPUT,
    create_country_metrics,
    create_product_benchmark,
    load_clean_data,
)


PROCESSED_CATALOG = PROJECT_ROOT / "data" / "processed_catalog.csv"

PROCESSED_COLUMNS = {
    "unique_id",
    "product_id",
    "product_name",
    "main_category",
    "sub_category",
    "product_rating",
    "online_sellable",
    "country",
    "price_usd",
    "gdp_per_capita",
}

COUNTRY_METRICS_COLUMNS = {
    "country",
    "region",
    "avg_price_usd",
    "avg_rating",
    "total_products",
    "unique_categories",
    "price_standard_deviation",
    "gdp_per_capita",
    "online_availability_pct",
    "assortment_breadth",
    "global_avg_price",
    "price_index",
    "affordability_index",
}

PRODUCT_BENCHMARK_COLUMNS = {
    "country",
    "product_name",
    "product_avg_price_usd",
    "product_avg_rating",
    "listings",
}


def assert_has_columns(df: pd.DataFrame, expected_columns: set[str]) -> None:
    missing_columns = expected_columns.difference(df.columns)
    assert not missing_columns, f"Missing columns: {sorted(missing_columns)}"


def test_generated_pipeline_csv_outputs_have_expected_shape() -> None:
    processed_df = pd.read_csv(PROCESSED_CATALOG)
    country_df = pd.read_csv(COUNTRY_OUTPUT)
    benchmark_df = pd.read_csv(BENCHMARK_OUTPUT)

    assert_has_columns(processed_df, PROCESSED_COLUMNS)
    assert_has_columns(country_df, COUNTRY_METRICS_COLUMNS)
    assert_has_columns(benchmark_df, PRODUCT_BENCHMARK_COLUMNS)

    assert len(processed_df) >= 300_000
    assert processed_df["country"].nunique() >= 40
    assert processed_df["price_usd"].gt(0).all()

    assert len(country_df) >= 40
    assert country_df["country"].nunique() == len(country_df)
    assert country_df["avg_price_usd"].gt(0).all()
    assert country_df["price_index"].gt(0).all()
    assert country_df["gdp_per_capita"].notna().all()
    assert country_df["gdp_per_capita"].gt(0).all()
    assert country_df["affordability_index"].notna().all()
    assert country_df["affordability_index"].ge(0).all()
    assert country_df["online_availability_pct"].between(0, 100).all()

    assert len(benchmark_df) >= 100_000
    assert benchmark_df["product_avg_price_usd"].gt(0).all()
    assert benchmark_df["listings"].ge(1).all()


def test_aggregation_helpers_rebuild_expected_output_shapes() -> None:
    clean_df = load_clean_data()
    country_df = create_country_metrics(clean_df)
    benchmark_df = create_product_benchmark(clean_df)

    assert_has_columns(country_df, COUNTRY_METRICS_COLUMNS)
    assert_has_columns(benchmark_df, PRODUCT_BENCHMARK_COLUMNS)

    assert len(country_df) >= 40
    assert country_df["country"].nunique() == len(country_df)
    assert country_df["price_index"].gt(0).all()
    assert country_df["gdp_per_capita"].notna().all()
    assert country_df["affordability_index"].notna().all()

    assert len(benchmark_df) >= 100_000
    assert benchmark_df["product_name"].nunique() >= 1_000
    assert benchmark_df["listings"].ge(1).all()
