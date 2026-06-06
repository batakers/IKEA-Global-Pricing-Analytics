from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.clustering import ARTIFACT_FILE, COUNTRY_FILE, METADATA_FILE, OUTPUT_FILE, persist_clustering_artifacts


def main() -> None:
    if not COUNTRY_FILE.exists():
        raise FileNotFoundError(f"Missing file: {COUNTRY_FILE}")

    country_df = pd.read_csv(COUNTRY_FILE)
    clustering_df = persist_clustering_artifacts(country_df)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    clustering_df.to_csv(OUTPUT_FILE, index=False)

    print("Market Clustering Results:")
    print(clustering_df.groupby("cluster_label").size())
    print(f"\nSaved to: {OUTPUT_FILE}")
    print(f"Saved artifact to: {ARTIFACT_FILE}")
    print(f"Saved metadata to: {METADATA_FILE}")


if __name__ == "__main__":
    main()
