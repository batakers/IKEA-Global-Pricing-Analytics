from __future__ import annotations

from pathlib import Path
import sys
import pytest
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data_prep import normalize_bool, parse_numeric, standardize_country
from src.schemas import CountryMetricsSchema, ProductBenchmarkSchema


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_country_metrics():
    """Sample valid country metrics for testing."""
    return {
        "country": "United States",
        "region": "North America",
        "avg_price_usd": 201.88,
        "avg_rating": 3.8,
        "total_products": 500,
        "unique_categories": 25,
        "global_avg_price": 176.50,
        "price_index": 201.88 / 176.50,  # Calculate actual value
        "affordability_index": 201.88 / 81695.0,  # Calculate actual value
        "price_standard_deviation": 150.5,
        "gdp_per_capita": 81695,
        "online_availability_pct": 92.5,
        "assortment_breadth": 120,
    }


# ============================================================================
# TESTS: DATA PARSING
# ============================================================================

class TestDataCleaning:
    """Tests for data cleaning and parsing functions."""
    
    def test_parse_numeric_valid(self):
        """Test parsing valid numeric strings."""
        assert parse_numeric("123.45") == 123.45
        assert parse_numeric("1000") == 1000.0
        assert parse_numeric("0.99") == 0.99
    
    def test_parse_numeric_with_currency(self):
        """Test parsing numeric strings with currency symbols."""
        assert parse_numeric("$99.99") == 99.99
        assert parse_numeric("EUR 150.50") == 150.50
    
    def test_parse_numeric_invalid(self):
        """Test parsing invalid inputs returns NaN."""
        result = parse_numeric("invalid")
        assert pd.isna(result)
    
    def test_parse_numeric_empty(self):
        """Test parsing empty values."""
        assert pd.isna(parse_numeric(None))
        assert pd.isna(parse_numeric(""))
    
    def test_normalize_bool_true(self):
        """Test boolean normalization for true values."""
        assert normalize_bool("true") is True
        assert normalize_bool("1") is True
        assert normalize_bool("yes") is True
    
    def test_normalize_bool_false(self):
        """Test boolean normalization for false values."""
        assert normalize_bool("false") is False
        assert normalize_bool("0") is False
        assert normalize_bool("no") is False
    
    def test_normalize_bool_invalid(self):
        """Test invalid boolean returns NaN."""
        assert pd.isna(normalize_bool("maybe"))
    
    def test_standardize_country_standard(self):
        """Test country name standardization."""
        assert standardize_country("united states") == "United States"
        assert standardize_country("SWEDEN") == "Sweden"
    
    def test_standardize_country_alias(self):
        """Test country name alias resolution."""
        assert standardize_country("usa") == "United States"
        assert standardize_country("uk") == "United Kingdom"


# ============================================================================
# TESTS: PYDANTIC SCHEMAS
# ============================================================================

class TestCountryMetricsValidation:
    """Tests for CountryMetricsSchema validation."""
    
    def test_valid_country_metrics(self, sample_country_metrics):
        """Test validation of valid country metrics."""
        schema = CountryMetricsSchema(**sample_country_metrics)
        assert schema.country == "United States"
        assert abs(schema.price_index - 1.14) < 0.01  # Allow for floating point approximation
    
    def test_invalid_price_too_high(self, sample_country_metrics):
        """Test validation rejects unrealistic prices."""
        sample_country_metrics["avg_price_usd"] = 50000
        with pytest.raises(ValueError):
            CountryMetricsSchema(**sample_country_metrics)
    
    def test_invalid_rating_out_of_range(self, sample_country_metrics):
        """Test validation rejects ratings outside 0-5 range."""
        sample_country_metrics["avg_rating"] = 6.5
        with pytest.raises(ValueError):
            CountryMetricsSchema(**sample_country_metrics)
    
    def test_missing_required_field(self, sample_country_metrics):
        """Test validation enforces required fields."""
        del sample_country_metrics["country"]
        with pytest.raises(ValueError):
            CountryMetricsSchema(**sample_country_metrics)


class TestProductBenchmarkValidation:
    """Tests for ProductBenchmarkSchema validation."""
    
    def test_valid_product_benchmark(self):
        """Test validation of valid benchmark."""
        benchmark = ProductBenchmarkSchema(
            country="United States",
            product_name="BILLY",
            product_avg_price_usd=89.99,
            product_avg_rating=4.5,
            listings=3,
        )
        assert benchmark.product_name == "BILLY"
    
    def test_invalid_negative_price(self):
        """Test validation rejects negative prices."""
        with pytest.raises(ValueError):
            ProductBenchmarkSchema(
                country="US",
                product_name="TEST",
                product_avg_price_usd=-10.0,
                product_avg_rating=3.0,
                listings=1,
            )


# ============================================================================
# TESTS: BUSINESS LOGIC
# ============================================================================

class TestBusinessLogic:
    """Tests for core business logic."""
    
    def test_price_index_calculation(self, sample_country_metrics):
        """Validate price index meaning."""
        metrics = CountryMetricsSchema(**sample_country_metrics)
        assert metrics.price_index == metrics.avg_price_usd / metrics.global_avg_price
        assert metrics.price_index > 1.0  # Premium market
    
    def test_affordability_index_meaning(self, sample_country_metrics):
        """Validate affordability logic."""
        metrics = CountryMetricsSchema(**sample_country_metrics)
        assert metrics.affordability_index > 0
        assert metrics.affordability_index == metrics.avg_price_usd / metrics.gdp_per_capita


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
