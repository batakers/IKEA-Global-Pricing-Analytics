from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_prep import normalize_bool, parse_numeric, standardize_country

DATA_DIR = PROJECT_ROOT / "data"
CATALOG_FILE = DATA_DIR / "IKEA_product_catalog.csv"
EXCHANGE_FILE = DATA_DIR / "exchange_rate.csv"
GDP_FILE = DATA_DIR / "gdp_per_capita.csv"
OUTPUT_FILE = DATA_DIR / "processed_catalog.csv"


REQUIRED_CATALOG_COLUMNS = {
    "product_id",
    "product_name",
    "main_category",
    "product_rating",
    "online_sellable",
    "price",
    "currency",
    "country",
}
def _find_exchange_rate_column(exchange_df: pd.DataFrame) -> str:
    candidate_columns = ["usd_rate", "exchange_rate", "rate_to_usd", "usd_conversion_rate"]
    lowered = {col.lower(): col for col in exchange_df.columns}

    for candidate in candidate_columns:
        if candidate in lowered:
            return lowered[candidate]

    raise ValueError(
        "exchange_rate.csv must include one of these columns: "
        "usd_rate, exchange_rate, rate_to_usd, usd_conversion_rate"
    )



def _find_gdp_column(gdp_df: pd.DataFrame) -> str:
    candidate_columns = ["gdp_per_capita", "gdp_capita", "gdp_per_person", "gdp_pc"]
    lowered = {col.lower(): col for col in gdp_df.columns}

    for candidate in candidate_columns:
        if candidate in lowered:
            return lowered[candidate]

    raise ValueError(
        "gdp_per_capita.csv must include one of these columns: "
        "gdp_per_capita, gdp_capita, gdp_per_person, gdp_pc"
    )



def load_input_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not CATALOG_FILE.exists():
        raise FileNotFoundError(f"Missing file: {CATALOG_FILE}")
    if not EXCHANGE_FILE.exists():
        raise FileNotFoundError(f"Missing file: {EXCHANGE_FILE}")
    if not GDP_FILE.exists():
        raise FileNotFoundError(f"Missing file: {GDP_FILE}")

    catalog_df = pd.read_csv(CATALOG_FILE)
    exchange_df = pd.read_csv(EXCHANGE_FILE)
    gdp_df = pd.read_csv(GDP_FILE)

    return catalog_df, exchange_df, gdp_df



def prepare_catalog(catalog_df: pd.DataFrame, exchange_df: pd.DataFrame, gdp_df: pd.DataFrame) -> pd.DataFrame:
    missing_columns = REQUIRED_CATALOG_COLUMNS.difference(catalog_df.columns)
    if missing_columns:
        raise ValueError(f"IKEA_product_catalog.csv is missing columns: {sorted(missing_columns)}")

    df = catalog_df.copy()

    df["country"] = df["country"].apply(standardize_country)
    df["price"] = df["price"].apply(parse_numeric)
    df["product_rating"] = df["product_rating"].apply(parse_numeric)
    df["online_sellable"] = df["online_sellable"].apply(normalize_bool)

    # Keep one record per product-country pair to avoid double-counting in country analysis.
    duplicate_subset = ["product_id", "country"]
    if "unique_id" in df.columns:
        duplicate_subset = ["unique_id"]
    df = df.drop_duplicates(subset=duplicate_subset)

    # Business-critical fields for pricing analysis: remove rows where pricing keys are absent.
    df = df.dropna(subset=["country", "currency", "price", "product_id"])

    # Fill rating gaps using country median first, then global median for stability.
    country_rating_median = df.groupby("country")["product_rating"].transform("median")
    global_rating_median = df["product_rating"].median()
    df["product_rating"] = df["product_rating"].fillna(country_rating_median).fillna(global_rating_median)

    # Fill non-critical dimensions with explicit "Unknown" to keep rows analyzable.
    fill_unknown_columns = ["main_category", "sub_category", "product_type", "product_measurements"]
    for column in fill_unknown_columns:
        if column in df.columns:
            df[column] = df[column].fillna("Unknown")

    if "online_sellable" in df.columns:
        df["online_sellable"] = df["online_sellable"].fillna(False)

    exchange = exchange_df.copy()
    exchange.columns = [col.strip() for col in exchange.columns]
    if "currency" not in exchange.columns:
        raise ValueError("exchange_rate.csv must include a 'currency' column")

    rate_column = _find_exchange_rate_column(exchange)
    exchange["currency"] = exchange["currency"].astype(str).str.strip().str.upper()
    exchange[rate_column] = exchange[rate_column].apply(parse_numeric)
    exchange = exchange.dropna(subset=["currency", rate_column])

    df["currency"] = df["currency"].astype(str).str.strip().str.upper()
    df = df.merge(exchange[["currency", rate_column]], on="currency", how="left")
    df["price_usd"] = df["price"] * df[rate_column]
    df = df.dropna(subset=["price_usd"])

    gdp = gdp_df.copy()
    gdp.columns = [col.strip() for col in gdp.columns]
    if "country" not in gdp.columns:
        raise ValueError("gdp_per_capita.csv must include a 'country' column")

    gdp_column = _find_gdp_column(gdp)
    gdp["country"] = gdp["country"].apply(standardize_country)
    gdp[gdp_column] = gdp[gdp_column].apply(parse_numeric)
    gdp = gdp.dropna(subset=["country", gdp_column])

    df = df.merge(gdp[["country", gdp_column]], on="country", how="left")
    df = df.rename(columns={gdp_column: "gdp_per_capita", rate_column: "usd_rate"})

    # Clamp invalid ratings into a business-plausible range.
    df["product_rating"] = df["product_rating"].clip(lower=0, upper=5)

    return df



def main() -> None:
    catalog_df, exchange_df, gdp_df = load_input_data()
    clean_df = prepare_catalog(catalog_df, exchange_df, gdp_df)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    clean_df.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved cleaned dataset to: {OUTPUT_FILE}")
    print(f"Rows: {len(clean_df):,}")
    print(f"Countries: {clean_df['country'].nunique():,}")
    print(f"Missing GDP rows: {clean_df['gdp_per_capita'].isna().sum():,}")


if __name__ == "__main__":
    main()
