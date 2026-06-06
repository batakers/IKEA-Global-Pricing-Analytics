from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
INPUT_FILE = DATA_DIR / "processed_catalog.csv"
COUNTRY_OUTPUT = DATA_DIR / "country_metrics.csv"
BENCHMARK_OUTPUT = DATA_DIR / "product_benchmark.csv"


REGION_MAP = {
    "Australia": "Oceania",
    "Austria": "Europe",
    "Bahrain": "Middle East",
    "Belgium": "Europe",
    "Bulgaria": "Europe",
    "Canada": "North America",
    "China": "Asia",
    "Croatia": "Europe",
    "Cyprus": "Europe",
    "Czechia": "Europe",
    "Denmark": "Europe",
    "Dominican Republic": "Caribbean",
    "Egypt": "Africa",
    "Estonia": "Europe",
    "Finland": "Europe",
    "France": "Europe",
    "Germany": "Europe",
    "Greece": "Europe",
    "Hungary": "Europe",
    "Iceland": "Europe",
    "India": "Asia",
    "Indonesia": "Asia",
    "Ireland": "Europe",
    "Israel": "Middle East",
    "Italy": "Europe",
    "Japan": "Asia",
    "Jordan": "Middle East",
    "Korea, Republic Of": "Asia",
    "Kuwait": "Middle East",
    "Latvia": "Europe",
    "Lithuania": "Europe",
    "Malaysia": "Asia",
    "Morocco": "Africa",
    "Netherlands": "Europe",
    "New Zealand": "Oceania",
    "Norway": "Europe",
    "Oman": "Middle East",
    "Philippines": "Asia",
    "Poland": "Europe",
    "Portugal": "Europe",
    "Puerto Rico": "Caribbean",
    "Qatar": "Middle East",
    "Romania": "Europe",
    "Saudi Arabia": "Middle East",
    "Serbia": "Europe",
    "Singapore": "Asia",
    "Slovakia": "Europe",
    "Slovenia": "Europe",
    "Spain": "Europe",
    "Sweden": "Europe",
    "Switzerland": "Europe",
    "Taiwan": "Asia",
    "Thailand": "Asia",
    "Turkey": "Europe",
    "United Arab Emirates": "Middle East",
    "United Kingdom": "Europe",
    "United States": "North America",
    "Vietnam": "Asia",
}


def load_clean_data() -> pd.DataFrame:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Missing file: {INPUT_FILE}. Run 01_data_preparation.py first.")

    return pd.read_csv(INPUT_FILE)


def create_country_metrics(df: pd.DataFrame) -> pd.DataFrame:
    country_df = df.copy()
    country_df["region"] = country_df["country"].map(REGION_MAP).fillna("Other")

    global_avg_price = country_df["price_usd"].mean()

    metrics = (
        country_df.groupby(["country", "region"], as_index=False)
        .agg(
            avg_price_usd=("price_usd", "mean"),
            avg_rating=("product_rating", "mean"),
            total_products=("product_id", "nunique"),
            unique_categories=("main_category", "nunique"),
            price_standard_deviation=("price_usd", "std"),
            gdp_per_capita=("gdp_per_capita", "mean"),
            online_availability_pct=("online_sellable", lambda s: float(np.mean(s.astype(float)) * 100)),
            assortment_breadth=("sub_category", "nunique"),
        )
        .sort_values("avg_price_usd", ascending=False)
    )

    metrics["global_avg_price"] = global_avg_price
    metrics["price_index"] = metrics["avg_price_usd"] / metrics["global_avg_price"]
    metrics["affordability_index"] = metrics["avg_price_usd"] / metrics["gdp_per_capita"]
    metrics["price_standard_deviation"] = metrics["price_standard_deviation"].fillna(0)

    return metrics


def create_product_benchmark(df: pd.DataFrame) -> pd.DataFrame:
    benchmark = (
        df.groupby(["country", "product_name"], as_index=False)
        .agg(
            product_avg_price_usd=("price_usd", "mean"),
            product_avg_rating=("product_rating", "mean"),
            listings=("product_id", "count"),
        )
        .sort_values(["product_name", "product_avg_price_usd"], ascending=[True, False])
    )
    return benchmark


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