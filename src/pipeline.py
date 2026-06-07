from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
MANIFEST_FILE = DATA_DIR / "pipeline_manifest.json"
GITHUB_FILE_LIMIT_BYTES = 100_000_000

PROCESSED_CATALOG = DATA_DIR / "processed_catalog.csv"
COUNTRY_METRICS = DATA_DIR / "country_metrics.csv"
PRODUCT_BENCHMARK = DATA_DIR / "product_benchmark.csv"
CLUSTERING_RESULTS = DATA_DIR / "clustering_results.csv"
CLUSTERING_ARTIFACT = DATA_DIR / "clustering_artifact.joblib"
CLUSTERING_METADATA = DATA_DIR / "clustering_metadata.json"
CLUSTERING_EVALUATION = DATA_DIR / "clustering_evaluation.json"

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

CLUSTERING_COLUMNS = {
    "country",
    "region",
    "price_index",
    "affordability_index",
    "cluster_id",
    "silhouette_score",
    "cluster_label",
}

EXPECTED_CLUSTER_LABELS = {"Premium Markets", "Emerging Markets", "Niche Markets"}

LINEAGE = [
    {
        "step": "data_preparation",
        "inputs": ["data/IKEA_product_catalog.csv", "data/exchange_rate.csv", "data/gdp_per_capita.csv"],
        "outputs": ["data/processed_catalog.csv"],
    },
    {
        "step": "country_aggregation",
        "inputs": ["data/processed_catalog.csv"],
        "outputs": ["data/country_metrics.csv", "data/product_benchmark.csv"],
    },
    {
        "step": "market_clustering",
        "inputs": ["data/country_metrics.csv"],
        "outputs": ["data/clustering_results.csv", "data/clustering_artifact.joblib", "data/clustering_metadata.json"],
    },
    {
        "step": "cluster_validation",
        "inputs": ["data/country_metrics.csv", "data/clustering_results.csv"],
        "outputs": ["data/clustering_evaluation.json"],
    },
]


def relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def _json_default(value: Any) -> Any:
    if hasattr(value, "item"):
        value = value.item()

    if isinstance(value, float) and not math.isfinite(value):
        return None

    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _schema_hash(columns: list[str]) -> str:
    normalized = "|".join(columns)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _pass_check(name: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"name": name, "status": "pass", "details": details or {}}


def _fail_check(name: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = details or {}
    payload["message"] = message
    return {"name": name, "status": "fail", "details": payload}


def _check_columns(df: pd.DataFrame, expected_columns: set[str]) -> list[str]:
    return sorted(expected_columns.difference(df.columns))


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _csv_artifact_summary(path: Path, expected_columns: set[str]) -> dict[str, Any]:
    df = pd.read_csv(path)
    return {
        "path": relative_path(path),
        "size_bytes": path.stat().st_size,
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": list(df.columns),
        "schema_hash": _schema_hash(list(df.columns)),
        "missing_expected_columns": _check_columns(df, expected_columns),
        "country_count": int(df["country"].nunique()) if "country" in df.columns else None,
    }


def _file_artifact_summary(path: Path) -> dict[str, Any]:
    return {
        "path": relative_path(path),
        "size_bytes": path.stat().st_size,
    }


def summarize_artifacts() -> dict[str, Any]:
    return {
        "processed_catalog": _csv_artifact_summary(PROCESSED_CATALOG, PROCESSED_COLUMNS),
        "country_metrics": _csv_artifact_summary(COUNTRY_METRICS, COUNTRY_METRICS_COLUMNS),
        "product_benchmark": _csv_artifact_summary(PRODUCT_BENCHMARK, PRODUCT_BENCHMARK_COLUMNS),
        "clustering_results": _csv_artifact_summary(CLUSTERING_RESULTS, CLUSTERING_COLUMNS),
        "clustering_artifact": _file_artifact_summary(CLUSTERING_ARTIFACT),
        "clustering_metadata": {
            **_file_artifact_summary(CLUSTERING_METADATA),
            "keys": sorted(_load_json(CLUSTERING_METADATA).keys()),
        },
        "clustering_evaluation": {
            **_file_artifact_summary(CLUSTERING_EVALUATION),
            "keys": sorted(_load_json(CLUSTERING_EVALUATION).keys()),
        },
    }


def validate_pipeline_outputs() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    required_files = [
        PROCESSED_CATALOG,
        COUNTRY_METRICS,
        PRODUCT_BENCHMARK,
        CLUSTERING_RESULTS,
        CLUSTERING_ARTIFACT,
        CLUSTERING_METADATA,
        CLUSTERING_EVALUATION,
    ]

    for path in required_files:
        if path.exists():
            checks.append(_pass_check(f"{relative_path(path)} exists", {"size_bytes": path.stat().st_size}))
        else:
            checks.append(_fail_check(f"{relative_path(path)} exists", "required artifact is missing"))

    if any(check["status"] == "fail" for check in checks):
        return checks

    processed_df = pd.read_csv(PROCESSED_CATALOG)
    country_df = pd.read_csv(COUNTRY_METRICS)
    benchmark_df = pd.read_csv(PRODUCT_BENCHMARK)
    clustering_df = pd.read_csv(CLUSTERING_RESULTS)
    metadata = _load_json(CLUSTERING_METADATA)
    evaluation = _load_json(CLUSTERING_EVALUATION)

    checks.extend(
        [
            _pass_check("processed_catalog schema", {"missing_columns": []})
            if not _check_columns(processed_df, PROCESSED_COLUMNS)
            else _fail_check("processed_catalog schema", "missing expected columns", {"missing_columns": _check_columns(processed_df, PROCESSED_COLUMNS)}),
            _pass_check("country_metrics schema", {"missing_columns": []})
            if not _check_columns(country_df, COUNTRY_METRICS_COLUMNS)
            else _fail_check("country_metrics schema", "missing expected columns", {"missing_columns": _check_columns(country_df, COUNTRY_METRICS_COLUMNS)}),
            _pass_check("product_benchmark schema", {"missing_columns": []})
            if not _check_columns(benchmark_df, PRODUCT_BENCHMARK_COLUMNS)
            else _fail_check("product_benchmark schema", "missing expected columns", {"missing_columns": _check_columns(benchmark_df, PRODUCT_BENCHMARK_COLUMNS)}),
            _pass_check("clustering_results schema", {"missing_columns": []})
            if not _check_columns(clustering_df, CLUSTERING_COLUMNS)
            else _fail_check("clustering_results schema", "missing expected columns", {"missing_columns": _check_columns(clustering_df, CLUSTERING_COLUMNS)}),
        ]
    )

    checks.append(
        _pass_check("processed_catalog row count", {"row_count": int(len(processed_df))})
        if len(processed_df) >= 300_000
        else _fail_check("processed_catalog row count", "expected at least 300,000 rows", {"row_count": int(len(processed_df))})
    )
    checks.append(
        _pass_check("processed_catalog country coverage", {"country_count": int(processed_df["country"].nunique())})
        if processed_df["country"].nunique() >= 40
        else _fail_check("processed_catalog country coverage", "expected at least 40 countries", {"country_count": int(processed_df["country"].nunique())})
    )
    checks.append(
        _pass_check("processed_catalog GitHub file size", {"size_bytes": PROCESSED_CATALOG.stat().st_size, "limit_bytes": GITHUB_FILE_LIMIT_BYTES})
        if PROCESSED_CATALOG.stat().st_size < GITHUB_FILE_LIMIT_BYTES
        else _fail_check("processed_catalog GitHub file size", "file exceeds GitHub 100 MB hard limit", {"size_bytes": PROCESSED_CATALOG.stat().st_size})
    )
    checks.append(
        _pass_check("price_usd positive", {"min_price_usd": float(processed_df["price_usd"].min())})
        if processed_df["price_usd"].gt(0).all()
        else _fail_check("price_usd positive", "found non-positive USD prices")
    )
    checks.append(
        _pass_check("country_metrics country uniqueness", {"row_count": int(len(country_df))})
        if country_df["country"].nunique() == len(country_df) and len(country_df) >= 40
        else _fail_check("country_metrics country uniqueness", "countries must be unique and at least 40")
    )
    checks.append(
        _pass_check("online availability bounds")
        if country_df["online_availability_pct"].between(0, 100).all()
        else _fail_check("online availability bounds", "online availability must be between 0 and 100")
    )
    checks.append(
        _pass_check("product_benchmark row count", {"row_count": int(len(benchmark_df))})
        if len(benchmark_df) >= 100_000
        else _fail_check("product_benchmark row count", "expected at least 100,000 benchmark rows", {"row_count": int(len(benchmark_df))})
    )
    checks.append(
        _pass_check("clustering cluster count", {"cluster_count": int(clustering_df["cluster_id"].nunique())})
        if clustering_df["cluster_id"].nunique() == 4
        else _fail_check("clustering cluster count", "expected exactly 4 cluster IDs", {"cluster_count": int(clustering_df["cluster_id"].nunique())})
    )
    checks.append(
        _pass_check("clustering labels", {"labels": sorted(clustering_df["cluster_label"].unique())})
        if set(clustering_df["cluster_label"]) == EXPECTED_CLUSTER_LABELS
        else _fail_check("clustering labels", "unexpected clustering labels", {"labels": sorted(clustering_df["cluster_label"].unique())})
    )
    checks.append(
        _pass_check("clustering metadata relative paths")
        if metadata.get("output_csv") == "data/clustering_results.csv" and metadata.get("input_csv") == "data/country_metrics.csv"
        else _fail_check("clustering metadata relative paths", "metadata paths must be repo-relative")
    )
    checks.append(
        _pass_check("clustering evaluation selected k", {"selected_cluster_count": evaluation.get("selected_cluster_count")})
        if evaluation.get("selected_cluster_count") == 4 and len(evaluation.get("evaluated_cluster_counts", [])) == 7
        else _fail_check("clustering evaluation selected k", "expected selected k=4 and seven evaluated k values")
    )
    checks.append(
        _pass_check("clustering evaluation drivers", {"top_driver": evaluation.get("feature_drivers", [{}])[0].get("feature")})
        if evaluation.get("feature_drivers", [{}])[0].get("feature") == "assortment_breadth"
        else _fail_check("clustering evaluation drivers", "expected assortment_breadth as top driver")
    )

    return checks


def build_pipeline_manifest(steps: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    checks = validate_pipeline_outputs()
    artifacts = summarize_artifacts()
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pipeline_name": "ikea-global-pricing-analytics",
        "status": status,
        "github_file_limit_bytes": GITHUB_FILE_LIMIT_BYTES,
        "steps": steps or [],
        "lineage": LINEAGE,
        "artifacts": artifacts,
        "checks": checks,
    }


def persist_pipeline_manifest(
    output_path: Path = MANIFEST_FILE,
    steps: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    manifest = build_pipeline_manifest(steps=steps)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, default=_json_default, allow_nan=False) + "\n", encoding="utf-8")
    return manifest


def assert_pipeline_healthy(manifest: dict[str, Any]) -> None:
    failed_checks = [check for check in manifest["checks"] if check["status"] != "pass"]
    if failed_checks:
        failed_names = ", ".join(check["name"] for check in failed_checks)
        raise RuntimeError(f"Pipeline health checks failed: {failed_names}")
