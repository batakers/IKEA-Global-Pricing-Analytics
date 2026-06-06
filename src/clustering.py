from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
COUNTRY_FILE = DATA_DIR / "country_metrics.csv"
OUTPUT_FILE = DATA_DIR / "clustering_results.csv"
ARTIFACT_FILE = DATA_DIR / "clustering_artifact.joblib"
METADATA_FILE = DATA_DIR / "clustering_metadata.json"
FEATURE_COLUMNS = ["price_index", "affordability_index", "online_availability_pct", "assortment_breadth"]
RANDOM_SEED = 42
DEFAULT_CLUSTER_COUNT = 4


def _metadata_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def _prepare_features(country_df: pd.DataFrame, feature_means: dict[str, float] | None = None) -> pd.DataFrame:
    features = country_df[FEATURE_COLUMNS].copy()
    if feature_means is None:
        feature_means = {column: float(value) for column, value in features.mean().items()}

    return features.fillna(feature_means)


def _build_cluster_labels(cluster_centers: pd.DataFrame, n_clusters: int) -> dict[int, str | None]:
    return {
        0: "Premium Markets" if cluster_centers.loc[0, "price_index"] > cluster_centers["price_index"].median() else "Value Markets",
        1: "Premium Markets" if cluster_centers.loc[1, "price_index"] > cluster_centers["price_index"].median() else "Value Markets",
        2: "Emerging Markets" if n_clusters > 2 else "Balanced Markets",
        3: "Niche Markets" if n_clusters > 3 else None,
    }


def _build_clustering_result(
    country_df: pd.DataFrame,
    clusters: Any,
    cluster_labels: dict[int, str | None],
    silhouette: float,
) -> pd.DataFrame:
    result_df = country_df[["country", "region", "price_index", "affordability_index"]].copy()
    result_df["cluster_id"] = clusters
    result_df["silhouette_score"] = silhouette
    result_df["cluster_label"] = result_df["cluster_id"].map(cluster_labels)

    return result_df.sort_values("cluster_id")


def fit_market_clustering(country_df: pd.DataFrame, n_clusters: int = DEFAULT_CLUSTER_COUNT) -> tuple[pd.DataFrame, dict[str, Any]]:
    features = _prepare_features(country_df)
    feature_means = {column: float(value) for column, value in features.mean().items()}

    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    kmeans = KMeans(n_clusters=n_clusters, random_state=RANDOM_SEED, n_init=10)
    clusters = kmeans.fit_predict(features_scaled)
    silhouette = float(silhouette_score(features_scaled, clusters))

    cluster_centers = pd.DataFrame(scaler.inverse_transform(kmeans.cluster_centers_), columns=FEATURE_COLUMNS)
    cluster_labels = _build_cluster_labels(cluster_centers, n_clusters)
    result_df = _build_clustering_result(country_df, clusters, cluster_labels, silhouette)

    artifact = {
        "scaler": scaler,
        "model": kmeans,
        "feature_columns": FEATURE_COLUMNS,
        "feature_means": feature_means,
        "cluster_labels": cluster_labels,
        "cluster_count": n_clusters,
        "random_seed": RANDOM_SEED,
        "silhouette_score": silhouette,
    }
    return result_df, artifact


def perform_market_clustering(country_df: pd.DataFrame, n_clusters: int = DEFAULT_CLUSTER_COUNT) -> pd.DataFrame:
    """
    Segment IKEA markets into clusters based on pricing and affordability dimensions.

    Args:
        country_df: Country-level metrics DataFrame
        n_clusters: Number of market segments

    Returns:
        DataFrame with cluster assignments and analysis
    """
    result_df, _ = fit_market_clustering(country_df, n_clusters=n_clusters)
    return result_df


def predict_market_clusters(country_df: pd.DataFrame, artifact: dict[str, Any]) -> pd.DataFrame:
    feature_columns = artifact["feature_columns"]
    feature_means = artifact["feature_means"]
    scaler = artifact["scaler"]
    model = artifact["model"]

    features = country_df[feature_columns].copy().fillna(feature_means)
    features_scaled = scaler.transform(features)
    clusters = model.predict(features_scaled)

    return _build_clustering_result(
        country_df,
        clusters,
        artifact["cluster_labels"],
        float(artifact["silhouette_score"]),
    )


def load_clustering_artifact(artifact_path: Path = ARTIFACT_FILE) -> dict[str, Any]:
    return joblib.load(artifact_path)


def persist_clustering_artifacts(
    country_df: pd.DataFrame,
    artifact_path: Path = ARTIFACT_FILE,
    metadata_path: Path = METADATA_FILE,
    n_clusters: int = DEFAULT_CLUSTER_COUNT,
    output_csv_path: Path = OUTPUT_FILE,
) -> pd.DataFrame:
    clustering_df, artifact = fit_market_clustering(country_df, n_clusters=n_clusters)

    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, artifact_path)

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "feature_columns": FEATURE_COLUMNS,
        "cluster_count": n_clusters,
        "random_seed": RANDOM_SEED,
        "row_count": int(len(country_df)),
        "artifact_file": _metadata_path(artifact_path),
        "metadata_file": _metadata_path(metadata_path),
        "input_csv": _metadata_path(COUNTRY_FILE),
        "output_csv": _metadata_path(output_csv_path),
        "model_type": type(artifact["model"]).__name__,
        "scaler_type": type(artifact["scaler"]).__name__,
        "silhouette_score": artifact["silhouette_score"],
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    return clustering_df


def main() -> None:
    if not COUNTRY_FILE.exists():
        raise FileNotFoundError(f"Missing file: {COUNTRY_FILE}")

    country_df = pd.read_csv(COUNTRY_FILE)
    clustering_df = persist_clustering_artifacts(country_df, n_clusters=DEFAULT_CLUSTER_COUNT)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    clustering_df.to_csv(OUTPUT_FILE, index=False)

    print("Market Clustering Results:")
    print(clustering_df.groupby("cluster_label").size())
    print(f"\nSaved to: {OUTPUT_FILE}")
    print(f"Saved artifact to: {ARTIFACT_FILE}")
    print(f"Saved metadata to: {METADATA_FILE}")


if __name__ == "__main__":
    main()
