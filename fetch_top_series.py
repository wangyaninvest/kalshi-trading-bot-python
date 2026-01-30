"""
Fetch and document top Kalshi series by volume from specific categories.
Generates documentation files showing top 400 series per category.
"""
import os
import csv
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
from clients import KalshiHttpClient, Environment
from datetime import datetime
import bot_config

# Load environment variables from .env file
load_dotenv()
env = Environment.PROD if bot_config.ENVIRONMENT == "PROD" else Environment.DEMO
KEYID = os.getenv('DEMO_KEYID') if env == Environment.DEMO else os.getenv('PROD_KEYID')
KEYFILE = os.getenv('DEMO_KEYFILE') if env == Environment.DEMO else os.getenv('PROD_KEYFILE')

# Load and parse private key for API authentication
try:
    with open(KEYFILE, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None
        )
except FileNotFoundError:
    raise FileNotFoundError(f"Private key file not found at {KEYFILE}")
except Exception as e:
    raise Exception(f"Error loading private key: {str(e)}")

# Initialize Kalshi API client
client = KalshiHttpClient(
    key_id=KEYID,
    private_key=private_key,
    environment=env
)

# Categories to fetch series from
TARGET_CATEGORIES = [
    "Crypto",
    "Economics",
    "Financials",
    "Elections",
    "Science and Technology",
    "Politics",
    "Companies",
    "Health",
    "World",
    "Climate and Weather",
    "Entertainment",
    "Sports"
]

# Fetch top 400 series from each category
print("Fetching top 400 series from each category...")
top_series = []

for category in TARGET_CATEGORIES:
    print(f"  {category}...", end=" ", flush=True)
    cursor = None
    category_series = []
    
    # Paginate through all series in this category
    while True:
        try:
            response = client.get_series(limit=100, cursor=cursor, category=category, include_volume=True)
            series_batch = response.get('series', [])
            
            if not series_batch:
                break
            
            category_series.extend(series_batch)
            
            cursor = response.get('cursor')
            if not cursor:
                break
        except Exception as e:
            print(f"Error: {e}")
            break
    
    # Sort by trading volume (descending) and select top 400
    category_series.sort(key=lambda x: x.get('volume', 0), reverse=True)
    top_400 = category_series[:400]
    
    print(f"{len(category_series)} series, top 400 selected")
    top_series.extend(top_400)

print(f"\nTotal: {len(top_series)} series from top 200 of each category")

# Generate documentation files
print("Generating documentation...")

# Create markdown documentation
os.makedirs('data', exist_ok=True)
with open('data/TOP_SERIES.md', 'w') as f:
    # Write header
    f.write("# Top Kalshi Series by Volume (Top 400 per Category)\n\n")
    f.write(f"**Categories:** {', '.join(TARGET_CATEGORIES)}\n\n")
    f.write(f"**Selection Method:** Top 400 series from each category by volume\n\n")
    f.write(f"**Total series:** {len(top_series)}\n\n")
    f.write(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ({env.value.upper()} environment)*\n\n")
    f.write("---\n\n")
    
    # Group series by category for summary
    categorized = {}
    for series in top_series:
        category = series.get('category', 'Uncategorized')
        if category not in categorized:
            categorized[category] = []
        categorized[category].append(series)
    
    # Write category summary table
    f.write("## Summary by Category\n\n")
    f.write("| Category | Series Count | Total Volume |\n")
    f.write("|----------|--------------|---------------|\n")
    for category in sorted(categorized.keys()):
        count = len(categorized[category])
        total_volume = sum(s.get('volume', 0) for s in categorized[category])
        f.write(f"| {category} | {count} | ${total_volume:,} |\n")
    f.write("\n---\n\n")
    
    # Write full series listing
    f.write("## All Series (Top 400 per Category)\n\n")
    f.write("| Rank | Ticker | Title | Category | Volume |\n")
    f.write("|------|--------|-------|----------|--------|\n")
    
    for i, series in enumerate(top_series, 1):
        ticker = series.get('ticker', 'N/A')
        title = series.get('title', 'N/A')
        category = series.get('category', 'N/A')
        volume = series.get('volume', 0)
        f.write(f"| {i} | `{ticker}` | {title} | {category} | ${volume:,} |\n")

# Generate CSV file for programmatic access
os.makedirs('data', exist_ok=True)
with open('data/top_series.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Rank', 'Ticker', 'Title', 'Category', 'Volume'])
    
    for i, series in enumerate(top_series, 1):
        writer.writerow([
            i,
            series.get('ticker', 'N/A'),
            series.get('title', 'N/A'),
            series.get('category', 'N/A'),
            series.get('volume', 0)
        ])

print("✓ Generated data/TOP_SERIES.md and data/top_series.csv")
