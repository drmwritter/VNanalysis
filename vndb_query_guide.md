# VNDB API Queries to Test the Distribution Model

## 1. Get Total Visual Novel Count
**Query Purpose:** Find out how many visual novels are in the database total
**API Endpoint:** `POST https://api.vndb.org/kana/stats`
**No authentication needed for stats**

**Expected Response:**
```json
{
  "vn": <total_count>,
  "releases": <count>,
  ...
}
```

## 2. Count VNs by Popularity Ranges
**Query Purpose:** Count how many VNs fall into different popularity tiers
**API Endpoint:** `POST https://api.vndb.org/kana/vn`

**Query for VNs with high popularity (proxy for high sales):**
```json
{
  "filters": ["popularity", ">", 80],
  "fields": "id",
  "count": true
}
```

**Query for different popularity ranges:**
- Very popular (80-100): `["popularity", ">", 80]`
- Popular (60-80): `["and", ["popularity", ">", 60], ["popularity", "<=", 80]]`
- Medium (40-60): `["and", ["popularity", ">", 40], ["popularity", "<=", 60]]`
- Low (20-40): `["and", ["popularity", ">", 20], ["popularity", "<=", 40]]`
- Very low (0-20): `["popularity", "<=", 20]`

## 3. Get VNs with Vote/Rating Data
**Query Purpose:** Find VNs that have enough user engagement to estimate sales
**API Endpoint:** `POST https://api.vndb.org/kana/vn`

**Query for VNs with many votes (indicates sales):**
```json
{
  "filters": ["votecount", ">", 100],
  "fields": "id, title, votecount, rating",
  "sort": "votecount",
  "reverse": true,
  "results": 100
}
```

**Different votecount tiers to check:**
- 10,000+ votes: Very high sales (likely 500k+ copies)
- 1,000-10,000 votes: High sales (likely 100k-500k)
- 100-1,000 votes: Medium sales (likely 10k-100k)
- 10-100 votes: Low sales (likely 1k-10k)
- <10 votes: Very low sales (<1k)

## 4. Count by Release Language (Commercial indicator)
**Query Purpose:** Filter to commercial releases only
**API Endpoint:** `POST https://api.vndb.org/kana/vn`

**Query for commercial VNs (Japanese original):**
```json
{
  "filters": ["olang", "=", "ja"],
  "fields": "id",
  "count": true
}
```

**Query for English commercial releases:**
```json
{
  "filters": ["olang", "=", "en"],
  "fields": "id",
  "count": true
}
```

## 5. Filter by Length (Exclude demos/short games)
**Query Purpose:** Get only full-length commercial VNs
**API Endpoint:** `POST https://api.vndb.org/kana/vn`

**Query for medium to very long VNs:**
```json
{
  "filters": ["length", ">=", 3],
  "fields": "id",
  "count": true
}
```

Length values:
- 1: Very short (< 2 hours)
- 2: Short (2-10 hours)
- 3: Medium (10-30 hours)
- 4: Long (30-50 hours)
- 5: Very long (> 50 hours)

## 6. Combined Query: Commercial VNs Only
**Query Purpose:** Get realistic count of commercial visual novels
**API Endpoint:** `POST https://api.vndb.org/kana/vn`

**Query:**
```json
{
  "filters": ["and", 
    ["olang", "=", "ja"],
    ["length", ">=", 2],
    ["votecount", ">", 10]
  ],
  "fields": "id",
  "count": true
}
```

This filters for:
- Japanese original (commercial market)
- At least "short" length (excludes demos)
- At least 10 votes (has some user engagement)

## 7. Distribution Analysis Query
**Query Purpose:** Get actual vote count distribution
**API Endpoint:** `POST https://api.vndb.org/kana/vn`

**Get top VNs by votecount:**
```json
{
  "filters": ["votecount", ">", 0],
  "fields": "id, title, votecount, popularity",
  "sort": "votecount",
  "reverse": true,
  "results": 100,
  "page": 1
}
```

Then repeat with page 2, 3, etc. to build distribution.

## Python Script to Run These Queries

```python
import requests
import json
import time

BASE_URL = "https://api.vndb.org/kana"

def query_vndb(endpoint, payload):
    """Query VNDB API"""
    url = f"{BASE_URL}/{endpoint}"
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    time.sleep(0.1)  # Rate limiting
    return response.json()

# 1. Get database stats
stats = query_vndb("stats", {})
print(f"Total VNs in database: {stats.get('vn', 'N/A')}")

# 2. Count by votecount ranges
votecount_ranges = [
    (10000, None, "10k+"),
    (1000, 10000, "1k-10k"),
    (100, 1000, "100-1k"),
    (10, 100, "10-100"),
    (0, 10, "0-10")
]

for min_votes, max_votes, label in votecount_ranges:
    if max_votes:
        filters = ["and", ["votecount", ">", min_votes], ["votecount", "<=", max_votes]]
    else:
        filters = ["votecount", ">", min_votes]
    
    result = query_vndb("vn", {
        "filters": filters,
        "fields": "id",
        "count": true
    })
    print(f"VNs with {label} votes: {result.get('count', 0)}")

# 3. Commercial VNs only
commercial = query_vndb("vn", {
    "filters": ["and", 
        ["olang", "=", "ja"],
        ["length", ">=", 2]
    ],
    "fields": "id",
    "count": true
})
print(f"Commercial Japanese VNs (length >= short): {commercial.get('count', 0)}")

# 4. Get distribution of top 1000 VNs
print("\nGetting top 1000 VNs by votecount...")
all_vns = []
for page in range(1, 11):  # Get 10 pages of 100 = 1000 VNs
    result = query_vndb("vn", {
        "filters": ["votecount", ">", 0],
        "fields": "id, title, votecount, popularity, rating",
        "sort": "votecount",
        "reverse": True,
        "results": 100,
        "page": page
    })
    all_vns.extend(result.get('results', []))
    print(f"  Page {page}: {len(result.get('results', []))} VNs")
    time.sleep(0.5)

# Save to file
with open('vndb_top1000.json', 'w') as f:
    json.dump(all_vns, f, indent=2)

print(f"\nSaved {len(all_vns)} VNs to vndb_top1000.json")
```

## What to Look For

1. **Total VN count** - Is it anywhere near 1.7 million? (Spoiler: probably not!)
2. **Vote distribution** - How many VNs have 100+ votes? 1000+? 10000+?
3. **Votecount as sales proxy** - Roughly, votecount × 10-100 ≈ sales (very rough!)
4. **Commercial filter** - How many are actual commercial releases vs. fan games?

## Expected Reality Check

Based on Wikipedia saying ~24,000 VNs in VNDB (as of 2019):
- If true, 1.7 million is off by **70x**
- This suggests the logarithmic model breaks down badly at low sales
- The model was fitted on high-selling VNs (>100k) and doesn't extrapolate well

Run these queries and we can compare reality to the model!
