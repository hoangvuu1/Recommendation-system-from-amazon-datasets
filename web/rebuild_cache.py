#!/usr/bin/env python3
"""
Rebuild product cache từ parquet + item_title.jsonl
"""
import pickle
import json
from pathlib import Path
import pandas as pd

project_root = Path(__file__).parent
meta_ui_path = project_root / "meta_ui"
jsonl_path = project_root / "item_title.jsonl"
cache_file = project_root / "product_names_cache.pkl"

print("=" * 80)
print("REBUILD PRODUCT CACHE")
print("=" * 80)

# Step 1: Load từ parquet (lấy ảnh)
print("\n[1/2] Loading images từ meta_ui parquet...")
try:
    df_meta = pd.read_parquet(meta_ui_path)
    print(f"  ✓ Loaded {len(df_meta)} records từ parquet")
    print(f"  Columns: {df_meta.columns.tolist()}")
except Exception as e:
    print(f"  ✗ Error: {e}")
    exit(1)

# Step 2: Build cache from parquet
print("\n[2/2] Building cache from parquet...")

# Check for product_id column
product_id_col = None
for col in ['product_id', 'item_id', 'asin', 'id']:
    if col in df_meta.columns:
        product_id_col = col
        break

if not product_id_col:
    print(f"  ✗ No product ID column found. Available: {df_meta.columns.tolist()}")
    exit(1)

print(f"  Using column: {product_id_col}")

# Build product_map
product_map = {}
for _, row in df_meta.iterrows():
    try:
        item_id = str(row[product_id_col]).strip()
        title = str(row['title']).strip() if pd.notna(row['title']) else None
        
        image_url = None
        if 'images' in df_meta.columns and pd.notna(row['images']):
            image_url = str(row['images']).strip()
        
        if item_id and title:
            product_map[item_id] = {
                'title': title,
                'image_url': image_url
            }
    except Exception as e:
        pass

print(f"  ✓ Built mapping with {len(product_map)} products")

# Step 4: Save cache
print(f"\n[3/3] Saving cache to {cache_file.name}...")
try:
    with open(cache_file, 'wb') as f:
        pickle.dump(product_map, f)
    print(f"  ✓ Cache saved successfully")
except Exception as e:
    print(f"  ✗ Error: {e}")
    exit(1)

# Step 5: Verify
print("\n" + "=" * 80)
print("VERIFICATION")
print("=" * 80)

# Load and verify
with open(cache_file, 'rb') as f:
    loaded_map = pickle.load(f)

print(f"\n✓ Cache load success!")
print(f"  Total products: {len(loaded_map)}")

# Sample
print(f"\nSample products (first 5):")
for i, (iid, data) in enumerate(list(loaded_map.items())[:5]):
    title = data.get('title') if isinstance(data, dict) else data
    img = data.get('image_url') if isinstance(data, dict) else None
    print(f"\n  {i+1}. {iid}")
    print(f"     Title: {title[:60]}...")
    print(f"     Image: {'✓' if img else '✗'}")

print(f"\n✅ REBUILD COMPLETE!")
