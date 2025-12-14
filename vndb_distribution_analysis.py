import requests
import json
import time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

BASE_URL = "https://api.vndb.org/kana"

def query_vndb(endpoint, payload):
    """Query VNDB API with rate limiting"""
    url = f"{BASE_URL}/{endpoint}"
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    time.sleep(0.15)  # Rate limiting: ~6 requests per second
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

print("=" * 70)
print("VNDB Visual Novel Distribution Analysis")
print("=" * 70)

# We already have total stats
total_vns = 58868
print(f"\nTotal VNs in database: {total_vns:,}")

# Step 1: Count VNs by votecount ranges
print("\n" + "=" * 70)
print("STEP 1: Distribution by Vote Count (proxy for sales)")
print("=" * 70)

votecount_ranges = [
    (10000, None, "10,000+"),
    (5000, 10000, "5,000-10,000"),
    (2000, 5000, "2,000-5,000"),
    (1000, 2000, "1,000-2,000"),
    (500, 1000, "500-1,000"),
    (250, 500, "250-500"),
    (100, 250, "100-250"),
    (50, 100, "50-100"),
    (25, 50, "25-50"),
    (10, 25, "10-25"),
    (5, 10, "5-10"),
    (1, 5, "1-5"),
    (0, 1, "0-1")
]

votecount_data = []
for min_votes, max_votes, label in votecount_ranges:
    if max_votes:
        filters = ["and", ["votecount", ">", min_votes], ["votecount", "<=", max_votes]]
    else:
        filters = ["votecount", ">", min_votes]
    
    result = query_vndb("vn", {
        "filters": filters,
        "fields": "id",
        "count": True
    })
    
    if result:
        count = result.get('count', 0)
        votecount_data.append({
            'range': label,
            'min': min_votes,
            'max': max_votes if max_votes else 999999,
            'count': count
        })
        print(f"  {label:>15} votes: {count:>6,} VNs")

# Step 2: Count commercial VNs (Japanese origin, reasonable length)
print("\n" + "=" * 70)
print("STEP 2: Commercial Visual Novels")
print("=" * 70)

commercial_filters = [
    ("All Japanese VNs", ["olang", "=", "ja"]),
    ("Japanese + Short or longer", ["and", ["olang", "=", "ja"], ["length", ">=", 2]]),
    ("Japanese + Medium or longer", ["and", ["olang", "=", "ja"], ["length", ">=", 3]]),
    ("Japanese + Some engagement", ["and", ["olang", "=", "ja"], ["votecount", ">", 10]]),
    ("Japanese + Medium + Engagement", ["and", ["olang", "=", "ja"], ["length", ">=", 3], ["votecount", ">", 10]]),
]

commercial_data = []
for label, filters in commercial_filters:
    result = query_vndb("vn", {
        "filters": filters,
        "fields": "id",
        "count": True
    })
    
    if result:
        count = result.get('count', 0)
        commercial_data.append({'filter': label, 'count': count})
        print(f"  {label:40s}: {count:>6,} VNs")

# Step 3: Get top VNs by votecount for detailed analysis
print("\n" + "=" * 70)
print("STEP 3: Fetching top 500 VNs by vote count...")
print("=" * 70)

top_vns = []
for page in range(1, 6):  # 5 pages × 100 = 500 VNs
    result = query_vndb("vn", {
        "filters": ["votecount", ">", 0],
        "fields": "id, title, votecount, popularity, rating, olang, length",
        "sort": "votecount",
        "reverse": True,
        "results": 100,
        "page": page
    })
    
    if result and 'results' in result:
        top_vns.extend(result['results'])
        print(f"  Page {page}/5: Retrieved {len(result['results'])} VNs")
    else:
        print(f"  Page {page}/5: Failed to retrieve")
        break

# Save raw data
with open('vndb_top500.json', 'w') as f:
    json.dump(top_vns, f, indent=2)
print(f"\n  Saved {len(top_vns)} VNs to vndb_top500.json")

# Step 4: Analyze the distribution
print("\n" + "=" * 70)
print("STEP 4: Statistical Analysis")
print("=" * 70)

if top_vns:
    votecounts = [vn['votecount'] for vn in top_vns if vn.get('votecount')]
    
    print(f"\nTop 500 VNs Vote Count Statistics:")
    print(f"  Max:     {max(votecounts):>8,} votes")
    print(f"  Median:  {np.median(votecounts):>8,.0f} votes")
    print(f"  Mean:    {np.mean(votecounts):>8,.0f} votes")
    print(f"  Min:     {min(votecounts):>8,} votes")
    
    # Calculate estimated sales (very rough: votecount × 50-100)
    print(f"\nEstimated Sales (if votecount × 75 ≈ sales):")
    print(f"  #1 VN:   ~{max(votecounts) * 75:>9,} copies")
    print(f"  #500 VN: ~{min(votecounts) * 75:>9,} copies")

# Step 5: Compare to our logarithmic model
print("\n" + "=" * 70)
print("STEP 5: Comparison to Logarithmic Model")
print("=" * 70)

# Our model: y = 77.66 - 5.69 * ln(x)
# This predicted ~1.7 million VNs in the 1k-100k sales range

# Let's see how many VNs VNDB actually has in different "estimated sales" ranges
# Using votecount × 75 as rough sales estimate

sales_estimate_ranges = [
    (100000, None, "100k+"),
    (50000, 100000, "50k-100k"),
    (25000, 50000, "25k-50k"),
    (10000, 25000, "10k-25k"),
    (5000, 10000, "5k-10k"),
    (1000, 5000, "1k-5k"),
]

print("\nEstimated sales ranges (votecount × 75):")
print("Note: This is a VERY rough approximation!")

for min_sales, max_sales, label in sales_estimate_ranges:
    min_votes = min_sales // 75
    max_votes = max_sales // 75 if max_sales else None
    
    if max_votes:
        filters = ["and", ["votecount", ">", min_votes], ["votecount", "<=", max_votes]]
    else:
        filters = ["votecount", ">", min_votes]
    
    result = query_vndb("vn", {
        "filters": filters,
        "fields": "id",
        "count": True
    })
    
    if result:
        count = result.get('count', 0)
        print(f"  {label:>12} sales: {count:>6,} VNs (votecounts {min_votes:>5,}-{max_votes if max_votes else '∞':>5})")

# Reality check
print("\n" + "=" * 70)
print("REALITY CHECK: Model vs. Actual")
print("=" * 70)
print(f"\nLogarithmic model predicted: ~1,700,000 VNs (1k-100k sales)")
print(f"VNDB total database:         ~{total_vns:>9,} VNs")
print(f"Ratio:                        {1700000/total_vns:.1f}x overestimate!")
print("\nConclusion: The logarithmic model breaks down dramatically")
print("when extrapolated to lower sales ranges. The actual market")
print("is much more concentrated at the top than the model suggests.")

# Save summary data
summary = {
    'total_vns': total_vns,
    'votecount_distribution': votecount_data,
    'commercial_counts': commercial_data,
    'top_500_stats': {
        'max_votes': max(votecounts) if votecounts else 0,
        'median_votes': float(np.median(votecounts)) if votecounts else 0,
        'mean_votes': float(np.mean(votecounts)) if votecounts else 0,
        'min_votes': min(votecounts) if votecounts else 0
    }
}

with open('vndb_analysis_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print(f"\n{'=' * 70}")
print("Analysis complete! Files saved:")
print("  - vndb_top500.json (raw data)")
print("  - vndb_analysis_summary.json (summary)")
print("=" * 70)
