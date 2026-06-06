"""
Generate preview images for README.
Creates visual snapshots of the dashboard without needing live Streamlit.
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ASSET_DIR = PROJECT_ROOT / "assets" / "dashboard"
ASSET_DIR.mkdir(parents=True, exist_ok=True)

# Set style
sns.set_style("darkgrid")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10

print("Generating README preview images...")

# Load data
country_df = pd.read_csv(DATA_DIR / "country_metrics.csv")
print(f"✓ Loaded country metrics: {len(country_df)} countries")

# --- 1. WORLD MAP PREVIEW: Top 10 Most & Least Expensive ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

top_expensive = country_df.nlargest(10, 'avg_price_usd')[['country', 'avg_price_usd']].sort_values('avg_price_usd')
ax1.barh(top_expensive['country'], top_expensive['avg_price_usd'], color='#d62728')
ax1.set_xlabel('Average Price (USD)', fontsize=11, fontweight='bold')
ax1.set_title('🔴 Top 10 Most Expensive Markets', fontsize=12, fontweight='bold')
ax1.grid(axis='x', alpha=0.3)

top_cheap = country_df.nsmallest(10, 'avg_price_usd')[['country', 'avg_price_usd']].sort_values('avg_price_usd', ascending=False)
ax2.barh(top_cheap['country'], top_cheap['avg_price_usd'], color='#2ca02c')
ax2.set_xlabel('Average Price (USD)', fontsize=11, fontweight='bold')
ax2.set_title('🟢 Top 10 Cheapest Markets', fontsize=12, fontweight='bold')
ax2.grid(axis='x', alpha=0.3)

plt.tight_layout()
plt.savefig(ASSET_DIR / "dashboard_pricing_comparison.png", dpi=100, bbox_inches='tight', facecolor='white')
print(f"✓ Saved: dashboard_pricing_comparison.png")
plt.close()

# --- 2. PRICE INDEX vs AFFORDABILITY ---
fig, ax = plt.subplots(figsize=(12, 7))

scatter = ax.scatter(
    country_df['price_index'], 
    country_df['affordability_index'],
    s=country_df['total_products'] / 100,
    alpha=0.6,
    c=country_df['price_index'],
    cmap='RdYlGn_r',
    edgecolors='black',
    linewidth=0.5
)

# Annotate key countries
for idx, row in country_df.nlargest(5, 'price_index').iterrows():
    ax.annotate(row['country'], (row['price_index'], row['affordability_index']), 
                fontsize=8, xytext=(5, 5), textcoords='offset points')

ax.set_xlabel('Price Index (vs Global Average)', fontsize=11, fontweight='bold')
ax.set_ylabel('Affordability Index (Price ÷ GDP per Capita)', fontsize=11, fontweight='bold')
ax.set_title('Market Positioning: Premium vs Value-Oriented', fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.3)
cbar = plt.colorbar(scatter, ax=ax)
cbar.set_label('Price Index', fontweight='bold')

plt.tight_layout()
plt.savefig(ASSET_DIR / "dashboard_market_positioning.png", dpi=100, bbox_inches='tight', facecolor='white')
print(f"✓ Saved: dashboard_market_positioning.png")
plt.close()

# --- 3. AFFORDABILITY PRESSURE ---
fig, ax = plt.subplots(figsize=(12, 8))

affordability_rank = country_df.nlargest(15, 'affordability_index')[['country', 'affordability_index']].sort_values('affordability_index')
colors = plt.cm.RdYlGn_r(affordability_rank['affordability_index'] / affordability_rank['affordability_index'].max())

bars = ax.barh(affordability_rank['country'], affordability_rank['affordability_index'], color=colors)
ax.set_xlabel('Affordability Pressure Index', fontsize=11, fontweight='bold')
ax.set_title('⚠️ Markets with Highest Affordability Pressure\n(Higher = More Expensive Relative to Income)', 
             fontsize=12, fontweight='bold')
ax.grid(axis='x', alpha=0.3)

plt.tight_layout()
plt.savefig(ASSET_DIR / "dashboard_affordability_pressure.png", dpi=100, bbox_inches='tight', facecolor='white')
print(f"✓ Saved: dashboard_affordability_pressure.png")
plt.close()

# --- 4. ONLINE AVAILABILITY by Region ---
fig, ax = plt.subplots(figsize=(12, 6))

region_online = country_df.groupby('region')['online_availability_pct'].mean().sort_values(ascending=True)
colors_region = plt.cm.Blues(region_online / region_online.max())

bars = ax.barh(region_online.index, region_online.values, color=colors_region)
ax.set_xlabel('Avg Online Availability (%)', fontsize=11, fontweight='bold')
ax.set_title('E-Commerce Maturity by Region', fontsize=12, fontweight='bold')
ax.set_xlim(0, 100)
ax.grid(axis='x', alpha=0.3)

# Add value labels
for i, (idx, val) in enumerate(region_online.items()):
    ax.text(val + 2, i, f'{val:.1f}%', va='center', fontweight='bold')

plt.tight_layout()
plt.savefig(ASSET_DIR / "dashboard_online_availability.png", dpi=100, bbox_inches='tight', facecolor='white')
print(f"✓ Saved: dashboard_online_availability.png")
plt.close()

# --- 5. ASSORTMENT BREADTH ---
fig, ax = plt.subplots(figsize=(12, 8))

assortment_rank = country_df.nlargest(15, 'assortment_breadth')[['country', 'assortment_breadth']].sort_values('assortment_breadth')
colors_assort = plt.cm.Spectral(assortment_rank['assortment_breadth'] / assortment_rank['assortment_breadth'].max())

bars = ax.barh(assortment_rank['country'], assortment_rank['assortment_breadth'], color=colors_assort)
ax.set_xlabel('Number of Sub-Categories', fontsize=11, fontweight='bold')
ax.set_title('🏪 Markets with Widest Product Assortment', fontsize=12, fontweight='bold')
ax.grid(axis='x', alpha=0.3)

plt.tight_layout()
plt.savefig(ASSET_DIR / "dashboard_assortment_breadth.png", dpi=100, bbox_inches='tight', facecolor='white')
print(f"✓ Saved: dashboard_assortment_breadth.png")
plt.close()

# --- 6. KEY METRICS TABLE ---
fig, ax = plt.subplots(figsize=(14, 6))
ax.axis('tight')
ax.axis('off')

# Create summary table
summary_data = {
    'Metric': [
        'Total Countries',
        'Products Analyzed',
        'Global Avg Price',
        'Most Expensive',
        'Cheapest',
        'Price Range',
        'Highest Affordability Pressure',
        'Widest Assortment'
    ],
    'Value': [
        f"{len(country_df)}",
        f"{country_df['total_products'].sum():,}",
        f"${country_df['avg_price_usd'].mean():.2f}",
        f"{country_df.loc[country_df['avg_price_usd'].idxmax(), 'country']}: ${country_df['avg_price_usd'].max():.2f}",
        f"{country_df.loc[country_df['avg_price_usd'].idxmin(), 'country']}: ${country_df['avg_price_usd'].min():.2f}",
        f"${country_df['avg_price_usd'].min():.2f} - ${country_df['avg_price_usd'].max():.2f}",
        f"{country_df.loc[country_df['affordability_index'].idxmax(), 'country']}",
        f"{country_df.loc[country_df['assortment_breadth'].idxmax(), 'country']}"
    ]
}

summary_df = pd.DataFrame(summary_data)

table = ax.table(cellText=summary_df.values, colLabels=summary_df.columns,
                cellLoc='left', loc='center', colWidths=[0.4, 0.6])

table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 2.5)

# Style header
for i in range(len(summary_df.columns)):
    table[(0, i)].set_facecolor('#1f77b4')
    table[(0, i)].set_text_props(weight='bold', color='white')

# Alternate row colors
for i in range(1, len(summary_df) + 1):
    for j in range(len(summary_df.columns)):
        if i % 2 == 0:
            table[(i, j)].set_facecolor('#f0f2f6')
        else:
            table[(i, j)].set_facecolor('#ffffff')

plt.title('📊 Dashboard Key Metrics', fontsize=14, fontweight='bold', pad=20)
plt.savefig(ASSET_DIR / "dashboard_key_metrics.png", dpi=100, bbox_inches='tight', facecolor='white')
print(f"✓ Saved: dashboard_key_metrics.png")
plt.close()

print("\n✅ All preview images generated successfully!")
print(f"📁 Location: {DOCS_DIR}/")
print("\nGenerated files:")
print("  1. dashboard_pricing_comparison.png - Expensive vs Cheap Markets")
print("  2. dashboard_market_positioning.png - Price Index vs Affordability")
print("  3. dashboard_affordability_pressure.png - Affordability Analysis")
print("  4. dashboard_online_availability.png - E-Commerce Maturity")
print("  5. dashboard_assortment_breadth.png - Product Range by Country")
print("  6. dashboard_key_metrics.png - Summary Statistics Table")
