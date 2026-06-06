from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src import clustering as clustering_module  # noqa: E402
from src.clustering import COUNTRY_FILE, OUTPUT_FILE, perform_market_clustering  # noqa: E402
from src.schemas import ClusteringResultSchema  # noqa: E402


CLUSTERING_COLUMNS = {
    "country",
    "region",
    "price_index",
    "affordability_index",
    "cluster_id",
    "silhouette_score",
    "cluster_label",
}

EXPECTED_CLUSTER_LABELS = {
    "Premium Markets",
    "Emerging Markets",
    "Niche Markets",
}


def assert_clustering_shape(df: pd.DataFrame) -> None:
    missing_columns = CLUSTERING_COLUMNS.difference(df.columns)
    assert not missing_columns, f"Missing columns: {sorted(missing_columns)}"

    assert len(df) >= 40
    assert df["country"].is_unique
    assert df["cluster_id"].nunique() == 4
    assert set(df["cluster_label"]) == EXPECTED_CLUSTER_LABELS
    assert df["silhouette_score"].between(-1, 1).all()
    assert df["silhouette_score"].gt(0).all()


def test_generated_clustering_output_has_stable_columns_and_labels() -> None:
    clustering_df = pd.read_csv(OUTPUT_FILE)

    assert_clustering_shape(clustering_df)

    for record in clustering_df[["country", "cluster_id", "cluster_label", "silhouette_score"]].head(5).to_dict("records"):
        ClusteringResultSchema(**record)


def test_perform_market_clustering_rebuilds_current_dataset_shape() -> None:
    country_df = pd.read_csv(COUNTRY_FILE)
    clustering_df = perform_market_clustering(country_df, n_clusters=4)

    assert_clustering_shape(clustering_df)
    assert len(clustering_df) == len(country_df)


def test_clustering_artifacts_can_be_persisted_and_reloaded(tmp_path: Path) -> None:
    country_df = pd.read_csv(COUNTRY_FILE)
    artifact_path = tmp_path / "clustering_artifact.joblib"
    metadata_path = tmp_path / "clustering_metadata.json"

    clustering_df = clustering_module.persist_clustering_artifacts(
        country_df,
        artifact_path=artifact_path,
        metadata_path=metadata_path,
        n_clusters=4,
    )
    artifact = clustering_module.load_clustering_artifact(artifact_path)
    reloaded_df = clustering_module.predict_market_clusters(country_df, artifact)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    assert artifact_path.exists()
    assert metadata_path.exists()
    assert_clustering_shape(clustering_df)
    assert_clustering_shape(reloaded_df)
    assert list(reloaded_df.columns) == list(clustering_df.columns)
    assert len(reloaded_df) == len(country_df)
    assert metadata["feature_columns"] == clustering_module.FEATURE_COLUMNS
    assert metadata["cluster_count"] == 4
    assert metadata["random_seed"] == clustering_module.RANDOM_SEED

    expected = clustering_df.sort_values("country").reset_index(drop=True)
    actual = reloaded_df.sort_values("country").reset_index(drop=True)
    pd.testing.assert_series_equal(actual["cluster_id"], expected["cluster_id"])
    pd.testing.assert_series_equal(actual["cluster_label"], expected["cluster_label"])


def test_generated_clustering_artifacts_exist_with_expected_metadata() -> None:
    assert clustering_module.ARTIFACT_FILE.exists()
    assert clustering_module.METADATA_FILE.exists()

    metadata = json.loads(clustering_module.METADATA_FILE.read_text(encoding="utf-8"))
    assert metadata["feature_columns"] == clustering_module.FEATURE_COLUMNS
    assert metadata["cluster_count"] == 4
    assert metadata["random_seed"] == clustering_module.RANDOM_SEED
    assert metadata["output_csv"] == "data/clustering_results.csv"
