from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.clustering import (  # noqa: E402
    COUNTRY_FILE,
    EVALUATION_FILE,
    persist_clustering_evaluation,
)


def main() -> None:
    if not COUNTRY_FILE.exists():
        raise FileNotFoundError(f"Missing file: {COUNTRY_FILE}. Run 02_country_aggregation.py first.")

    country_df = pd.read_csv(COUNTRY_FILE)
    evaluation = persist_clustering_evaluation(country_df)

    print("Cluster validation summary:")
    print(f"Evaluated k values: {[row['cluster_count'] for row in evaluation['evaluated_cluster_counts']]}")
    print(f"Best k by silhouette: {evaluation['best_cluster_count_by_silhouette']}")
    print(f"Selected k: {evaluation['selected_cluster_count']}")
    print(f"Selected silhouette score: {evaluation['selected_silhouette_score']:.4f}")
    print("Top feature drivers:")
    for row in evaluation["feature_drivers"][:3]:
        print(
            f"  {row['rank']}. {row['feature']} "
            f"(separation={row['cluster_center_separation']:.4f}, "
            f"tree_importance={row['decision_tree_importance']:.4f})"
        )
    print(f"Saved evaluation to: {EVALUATION_FILE}")


if __name__ == "__main__":
    main()
