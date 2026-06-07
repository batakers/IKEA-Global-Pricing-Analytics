from __future__ import annotations

import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import (  # noqa: E402
    GITHUB_FILE_LIMIT_BYTES,
    MANIFEST_FILE,
    build_pipeline_manifest,
    persist_pipeline_manifest,
    validate_pipeline_outputs,
)


def test_pipeline_health_checks_pass_for_generated_outputs() -> None:
    checks = validate_pipeline_outputs()
    failed_checks = [check for check in checks if check["status"] != "pass"]

    assert not failed_checks
    assert any(check["name"] == "processed_catalog GitHub file size" for check in checks)
    file_size_check = next(check for check in checks if check["name"] == "processed_catalog GitHub file size")
    assert file_size_check["details"]["size_bytes"] < GITHUB_FILE_LIMIT_BYTES


def test_pipeline_manifest_contains_lineage_and_artifact_summaries() -> None:
    manifest = build_pipeline_manifest(steps=[{"name": "unit_test", "status": "pass"}])

    assert manifest["status"] == "pass"
    assert manifest["pipeline_name"] == "ikea-global-pricing-analytics"
    assert manifest["github_file_limit_bytes"] == GITHUB_FILE_LIMIT_BYTES
    assert [step["step"] for step in manifest["lineage"]] == [
        "data_preparation",
        "country_aggregation",
        "market_clustering",
        "cluster_validation",
    ]

    artifacts = manifest["artifacts"]
    assert artifacts["processed_catalog"]["row_count"] >= 300_000
    assert artifacts["country_metrics"]["country_count"] >= 40
    assert artifacts["product_benchmark"]["row_count"] >= 100_000
    assert artifacts["clustering_evaluation"]["path"] == "data/clustering_evaluation.json"


def test_persist_pipeline_manifest_writes_valid_json(tmp_path: Path) -> None:
    output_path = tmp_path / "pipeline_manifest.json"
    manifest = persist_pipeline_manifest(output_path=output_path, steps=[{"name": "unit_test", "status": "pass"}])
    loaded = json.loads(output_path.read_text(encoding="utf-8"))

    assert output_path.exists()
    assert loaded["status"] == "pass"
    assert loaded["generated_at"] == manifest["generated_at"]
    assert loaded["checks"]


def test_generated_pipeline_manifest_artifact_is_current_and_healthy() -> None:
    assert MANIFEST_FILE.exists()

    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    assert manifest["status"] == "pass"
    assert manifest["artifacts"]["processed_catalog"]["row_count"] >= 300_000
    assert manifest["artifacts"]["clustering_evaluation"]["path"] == "data/clustering_evaluation.json"
    assert all(check["status"] == "pass" for check in manifest["checks"])
