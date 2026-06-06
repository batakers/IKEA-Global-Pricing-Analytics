from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import List
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pydantic import BaseModel

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.schemas import CountryMetricsSchema, ProductBenchmarkSchema, ClusteringResultSchema


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

country_metrics_df = pd.DataFrame()
product_benchmark_df = pd.DataFrame()
clustering_df = pd.DataFrame()


# ============================================================================
# SHARED UTILITIES
# ============================================================================


def load_data_from_directory(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    missing_files = [
        filename
        for filename in ("country_metrics.csv", "product_benchmark.csv", "clustering_results.csv")
        if not (data_dir / filename).exists()
    ]
    if missing_files:
        raise FileNotFoundError(
            "Required data outputs missing: " + ", ".join(missing_files)
        )

    return (
        pd.read_csv(data_dir / "country_metrics.csv"),
        pd.read_csv(data_dir / "product_benchmark.csv"),
        pd.read_csv(data_dir / "clustering_results.csv"),
    )


def load_data() -> None:
    """Load datasets into memory at startup."""
    global country_metrics_df, product_benchmark_df, clustering_df

    country_metrics, product_benchmark, clustering = load_data_from_directory(DATA_DIR)
    country_metrics_df = country_metrics
    product_benchmark_df = product_benchmark
    clustering_df = clustering


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_data()
    yield


app = FastAPI(
    title="IKEA Global Pricing API",
    description="Professional REST API for IKEA global pricing analytics",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for dashboard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# ENDPOINTS: COUNTRY METRICS
# ============================================================================

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "IKEA Pricing API"}


@app.get("/api/v1/countries", response_model=List[CountryMetricsSchema])
async def get_all_countries():
    """Retrieve metrics for all analyzed countries."""
    if country_metrics_df.empty:
        raise HTTPException(status_code=404, detail="No country data available")
    
    records = country_metrics_df.to_dict('records')
    return [CountryMetricsSchema(**record) for record in records]


@app.get("/api/v1/countries/{country_name}", response_model=CountryMetricsSchema)
async def get_country(country_name: str):
    """Retrieve metrics for a specific country."""
    match = country_metrics_df[country_metrics_df["country"].str.lower() == country_name.lower()]
    
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Country not found: {country_name}")
    
    return CountryMetricsSchema(**match.iloc[0].to_dict())


@app.get("/api/v1/countries/ranking/expensive")
async def top_expensive(limit: int = 10):
    """Top N most expensive countries by average price."""
    if country_metrics_df.empty:
        raise HTTPException(status_code=404, detail="No data available")
    
    top = country_metrics_df.nlargest(limit, "avg_price_usd")[["country", "avg_price_usd", "price_index"]]
    return top.to_dict(orient="records")


@app.get("/api/v1/countries/ranking/affordable")
async def top_affordable(limit: int = 10):
    """Top N most affordable countries."""
    if country_metrics_df.empty:
        raise HTTPException(status_code=404, detail="No data available")
    
    top = country_metrics_df.nsmallest(limit, "avg_price_usd")[["country", "avg_price_usd", "price_index"]]
    return top.to_dict(orient="records")


@app.get("/api/v1/countries/ranking/affordability-pressure")
async def affordability_pressure_ranking():
    """Countries ranked by affordability pressure (price / GDP per capita)."""
    if country_metrics_df.empty:
        raise HTTPException(status_code=404, detail="No data available")
    
    ranked = country_metrics_df.nlargest(10, "affordability_index")[["country", "affordability_index", "gdp_per_capita"]]
    return ranked.to_dict(orient="records")


# ============================================================================
# ENDPOINTS: PRODUCT BENCHMARKS
# ============================================================================

@app.get("/api/v1/products", response_model=List[ProductBenchmarkSchema])
async def get_all_benchmarks():
    """Retrieve all product benchmarks."""
    if product_benchmark_df.empty:
        raise HTTPException(status_code=404, detail="No benchmark data available")
    
    records = product_benchmark_df.to_dict('records')
    return [ProductBenchmarkSchema(**record) for record in records]


@app.get("/api/v1/products/{product_name}")
async def get_product_benchmark(product_name: str):
    """Get pricing for a specific product across all countries."""
    match = product_benchmark_df[product_benchmark_df["product_name"].str.upper() == product_name.upper()]
    
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Product not found: {product_name}")
    
    return match[["country", "product_avg_price_usd", "product_avg_rating"]].to_dict(orient="records")


# ============================================================================
# ENDPOINTS: MARKET CLUSTERING
# ============================================================================

@app.get("/api/v1/clustering", response_model=List[ClusteringResultSchema])
async def get_market_clusters():
    """Retrieve market clustering/segmentation results."""
    if clustering_df.empty:
        raise HTTPException(status_code=404, detail="Clustering data not available")
    
    records = clustering_df.to_dict('records')
    return [ClusteringResultSchema(**record) for record in records]


@app.get("/api/v1/clustering/{cluster_label}")
async def get_cluster_members(cluster_label: str):
    """Get all countries in a specific market cluster."""
    match = clustering_df[clustering_df["cluster_label"].str.lower() == cluster_label.lower()]
    
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Cluster not found: {cluster_label}")
    
    return match[["country", "region", "price_index", "affordability_index"]].to_dict(orient="records")


# ============================================================================
# ENDPOINTS: AGGREGATE STATISTICS
# ============================================================================

@app.get("/api/v1/statistics/global")
async def global_statistics():
    """Global pricing statistics."""
    if country_metrics_df.empty:
        raise HTTPException(status_code=404, detail="No data available")
    
    return {
        "total_countries": int(country_metrics_df["country"].nunique()),
        "average_price_usd": float(country_metrics_df["avg_price_usd"].mean()),
        "min_price_usd": float(country_metrics_df["avg_price_usd"].min()),
        "max_price_usd": float(country_metrics_df["avg_price_usd"].max()),
        "average_rating": float(country_metrics_df["avg_rating"].mean()),
        "online_availability_avg_pct": float(country_metrics_df["online_availability_pct"].mean()),
    }


@app.get("/api/v1/statistics/by-region/{region}")
async def statistics_by_region(region: str):
    """Regional pricing statistics."""
    match = country_metrics_df[country_metrics_df["region"].str.lower() == region.lower()]
    
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Region not found: {region}")
    
    return {
        "region": region,
        "countries": len(match),
        "average_price_usd": float(match["avg_price_usd"].mean()),
        "average_rating": float(match["avg_rating"].mean()),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
