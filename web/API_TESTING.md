# Quick API Testing with cURL

Here are some example cURL commands to test the API endpoints.

## 1. Health Check

```bash
curl -X GET "http://localhost:8000/health"
```

**Expected response:**
```json
{
  "status": "healthy",
  "final_recommendations_loaded": true,
  "popular_items_loaded": true,
  "metadata_loaded": true,
  "content_based_engine_loaded": true
}
```

## 2. Get Popular Items

```bash
curl -X GET "http://localhost:8000/recommend/popular?top_k=5"
```

## 3. Get Recommendations for User

```bash
# Replace AXXXXXXXXXXX with actual user_id
curl -X GET "http://localhost:8000/recommend/user/AXXXXXXXXXXX?top_k=10"
```

## 4. Find Similar Products

```bash
# Replace BXXXXXXXXXXX with actual item_id
curl -X GET "http://localhost:8000/recommend/item/BXXXXXXXXXXX?top_k=10"
```

## 5. Get Recommendations for New User (Cold Start)

```bash
curl -X POST "http://localhost:8000/recommend/new-user?top_k=10" \
  -H "Content-Type: application/json" \
  -d '{
    "interactions": [
      {"item_id": "B00000JBLQ", "rating": 5},
      {"item_id": "B00004S7P0", "rating": 4},
      {"item_id": "B00008VF1V", "rating": 2}
    ],
    "top_k": 10
  }'
```

## 6. Get Product Metadata

```bash
curl -X GET "http://localhost:8000/metadata/B00000JBLQ"
```

## Using Swagger UI (Interactive)

For interactive testing, open your browser and navigate to:

```
http://localhost:8000/docs
```

This provides:
- ✅ Try-it-out buttons
- ✅ Parameter validation
- ✅ Request/response visualization
- ✅ Auto-generated documentation

## Alternative: Python Requests Library

```python
import requests

BASE_URL = "http://localhost:8000"

# Popular items
response = requests.get(f"{BASE_URL}/recommend/popular?top_k=20")
print(response.json())

# User recommendations
response = requests.get(f"{BASE_URL}/recommend/user/AXXXXXXXXXXX?top_k=10")
print(response.json())

# Similar items
response = requests.get(f"{BASE_URL}/recommend/item/BXXXXXXXXXXX?top_k=10")
print(response.json())

# Cold start
response = requests.post(
    f"{BASE_URL}/recommend/new-user",
    json={
        "interactions": [
            {"item_id": "B00000JBLQ", "rating": 5},
            {"item_id": "B00004S7P0", "rating": 4}
        ],
        "top_k": 10
    }
)
print(response.json())
```

## API Response Format

All responses follow this format:

```json
{
  "items": [
    {
      "rank": 1,
      "item_id": "B00000JBLQ",
      "score": 0.9234,
      "metadata": {
        "product_id": "B00000JBLQ",
        "title": "Product Title",
        "description": "Product description...",
        "features": ["Feature 1", "Feature 2"]
      }
    }
  ],
  "total": 1
}
```

## Error Handling

If an error occurs, you'll get a response like:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common errors:
- 400: Bad request (invalid parameters)
- 503: Service unavailable (data not loaded)
- 500: Internal server error
