#!/usr/bin/env python3
"""
Simulate API call - xem JSON response trông như thế nào
"""
import sys
import json
from pathlib import Path

# Add backend to path  
backend_path = Path(__file__).parent / "web" / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(Path(__file__).parent))

from web.backend.main import load_data, get_popular_items

print("=" * 80)
print("TEST POPULAR ITEMS API RESPONSE")
print("=" * 80)

# Initialize
print("\nInitializing...")
load_data()

# Simulate popular items call
print("\nFetching popular items...")
import asyncio

async def test():
    response = await get_popular_items(top_k=3)
    return response

result = asyncio.run(test())

print("\nJSON Response:")
print(json.dumps(result.dict(), indent=2, ensure_ascii=False))
