#!/usr/bin/env python3
"""
Test API response - kiểm tra xem API có trả về image_url không
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "web" / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(Path(__file__).parent))

# Import main module
from web.backend.main import get_item_metadata, load_data

print("=" * 80)
print("TEST API - Get Item Metadata")
print("=" * 80)

# Initialize
print("\nInitializing...")
load_data()

# Test items
test_items = [
    "B001S28Q4Q",     # Should have everything
    "B07RPQVH21",     # Should have everything
    "INVALID",        # Should be placeholder
]

print("\nTesting metadata fetch:")
for item_id in test_items:
    metadata = get_item_metadata(item_id)
    print(f"\n{item_id}:")
    print(f"  Title: {metadata.title[:60] if metadata.title else 'None'}")
    print(f"  Image: {'✓ ' + metadata.image_url[:80] if metadata.image_url else '✗ None'}")
    print(f"  Description: {'✓' if metadata.description else '✗'}")
