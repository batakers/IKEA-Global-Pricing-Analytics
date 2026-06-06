from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import api.main as api_main


def test_health_endpoint_starts_with_loaded_data():
    with TestClient(api_main.app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "IKEA Pricing API"}


def test_global_statistics_work_when_data_is_available():
    with TestClient(api_main.app) as client:
        response = client.get("/api/v1/statistics/global")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_countries"] > 0
    assert payload["average_price_usd"] > 0


def test_load_data_from_directory_raises_clear_error_when_outputs_are_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="Required data outputs missing: country_metrics.csv, product_benchmark.csv, clustering_results.csv"):
        api_main.load_data_from_directory(tmp_path)