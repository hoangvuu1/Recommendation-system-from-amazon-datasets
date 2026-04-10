#!/usr/bin/env python3
"""
Check product cache - xem bao nhiêu sản phẩm có ảnh
"""
import pickle
from pathlib import Path

cache_file = Path(__file__).parent / "product_names_cache.pkl"

print("=" * 80)
print("CHECK PRODUCT CACHE")
print("=" * 80)

with open(cache_file, 'rb') as f:
    product_map = pickle.load(f)

print(f"\nTotal products: {len(product_map)}")

# Count products with images
with_image = 0
without_image = 0

for iid, data in product_map.items():
    if isinstance(data, dict):
        image_url = data.get('image_url')
        if image_url:
            with_image += 1
        else:
            without_image += 1
    else:
        # Old format (string only)
        without_image += 1

print(f"\nProducts with images: {with_image} ({with_image/len(product_map)*100:.1f}%)")
print(f"Products without images: {without_image} ({without_image/len(product_map)*100:.1f}%)")

# Sample some without images
print(f"\n" + "=" * 80)
print("SAMPLE PRODUCTS WITHOUT IMAGES (first 10)")
print("=" * 80)

count = 0
for iid, data in product_map.items():
    if isinstance(data, dict):
        image_url = data.get('image_url')
        if not image_url:
            title = data.get('title', 'No title')
            print(f"\n{iid}")
            print(f"  Title: {title[:70]}...")
            print(f"  Image: {image_url}")
            count += 1
            if count >= 10:
                break
