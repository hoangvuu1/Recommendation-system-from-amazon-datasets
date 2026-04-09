# Part 5 - Demo Web

Giao diện web để demo toàn bộ hệ thống gợi ý (Recommendation System).

## Tech Stack

- **Backend**: FastAPI + Uvicorn
- **Frontend**: HTML5 + Vanilla JavaScript + Bootstrap 5
- **Data**: Parquet files (final_recommendations, popular_items, metadata)

## Cấu Trúc Thư Mục

```
web/
├── backend/
│   ├── main.py              # FastAPI app chính
│   ├── schemas.py           # Pydantic models cho API
│   ├── requirements.txt     # Python dependencies
│   └── __init__.py
├── frontend/
│   ├── index.html           # 🏠 Trang chủ - Popular Products
│   ├── recommend.html       # 👤 Gợi ý cho người dùng (Hybrid)
│   ├── similar.html         # 🔗 Sản phẩm tương tự (Content-based)
│   ├── coldstart.html       # ⭐ Người dùng mới (Content-based)
│   ├── style.css            # CSS chung cho tất cả trang
│   └── static/              # (tự động mount từ frontend/)
└── README.md                # File này
```

## Cài Đặt

### 1. Cài Đặt Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Đảm Bảo Dữ Liệu Đã Sẵn Sàng

Cần có các file:
- `../Hybrid/final_recommendations.parquet` - Gợi ý từ hệ thống Hybrid
- `../Hybrid/popular_items.parquet` - Sản phẩm phổ biến
- `../RS-20260405T032136Z-1-001/RS/meta_rs.parquet` (optional) - Metadata sản phẩm
- `../content_based/engine/embedding_matrix/` (optional) - Để dùng content-based
- `../content_based/engine/faiss/` (optional) - Vector DB

## Chạy Ứng Dụng

### Method 1: Chạy Backend + Mở Frontend trong Browser

```bash
# Terminal 1: Chạy backend
cd backend
python main.py
```

Backend sẽ chạy tại: **http://localhost:8000**
- API Docs (Swagger): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

```bash
# Terminal 2: Mở frontend trong browser
# Windows
start http://localhost:8000/index.html

# Linux/Mac
open http://localhost:8000/index.html
```

### Method 2: Sử dụng Python HTTP Server (cho frontend)

```bash
# Terminal 1: Chạy backend
cd backend
python main.py

# Terminal 2: Chạy simple HTTP server cho frontend
cd frontend
python -m http.server 8080
```

Sau đó mở: **http://localhost:8080**

## API Endpoints

### 1. Health Check
```
GET /health
```
Kiểm tra trạng thái của API và dữ liệu đã load chưa.

**Response:**
```json
{
  "status": "healthy",
  "final_recommendations_loaded": true,
  "popular_items_loaded": true,
  "metadata_loaded": true,
  "content_based_engine_loaded": true
}
```

### 2. Sản Phẩm Phổ Biến
```
GET /recommend/popular?top_k=20
```
Lấy top sản phẩm phổ biến nhất (cho trang chủ).

**Response:**
```json
{
  "items": [
    {
      "rank": 1,
      "item_id": "B00000JBLQ",
      "score": 0.9234,
      "metadata": {
        "product_id": "B00000JBLQ",
        "title": "Stapler...",
        "description": "Durable stapler...",
        "features": [...]
      }
    }
  ],
  "total": 20
}
```

### 3. Gợi Ý cho Người Dùng (Hybrid System)
```
GET /recommend/user/{user_id}?top_k=10
```
Nhận gợi ý từ hệ thống Hybrid (ALS + Content-based) cho một user cụ thể.

**Response:**
```json
{
  "user_id": "AXXXXXXXXXXX",
  "items": [...],
  "total": 10
}
```

### 4. Sản Phẩm Tương Tự (Content-Based)
```
GET /recommend/item/{item_id}?top_k=10
```
Tìm những sản phẩm tương tự dựa trên nội dung (embeddings).

**Response:**
```json
{
  "item_id": "B00000JBLQ",
  "similar_items": [...],
  "total": 10
}
```

### 5. Gợi Ý cho Người Dùng Mới (Cold Start)
```
POST /recommend/new-user?top_k=10
```
Tính gợi ý cho người dùng mới dựa trên những sản phẩm họ chọn (content-based).

**Request Body:**
```json
{
  "interactions": [
    {"item_id": "B00000JBLQ", "rating": 5},
    {"item_id": "B00004S7P0", "rating": 4},
    {"item_id": "B00008VF1V", "rating": 2}
  ],
  "top_k": 10
}
```

**Response:**
```json
{
  "items": [...],
  "total": 10
}
```

### 6. Metadata Sản Phẩm
```
GET /metadata/{item_id}
```
Lấy thông tin chi tiết của một sản phẩm.

**Response:**
```json
{
  "product_id": "B00000JBLQ",
  "title": "Stapler",
  "description": "Durable black stapler...",
  "features": [...]
}
```

## Frontend Pages

### 🏠 Trang Chủ (`index.html`)
- Hiển thị **Top 20 Popular Products**
- Các thống kê: Reviews, Products, Users, Average Rating
- Mỗi sản phẩm có link tới **Similar Products**

### 👤 Gợi Ý cho Người Dùng (`recommend.html`)
- Nhập `user_id` để lấy gợi ý
- Hiển thị Top 15 gợi ý từ Hybrid System
- Fallback: nếu user không có gợi ý, hiển thị sản phẩm phổ biến

### 🔗 Sản Phẩm Tương Tự (`similar.html`)
- Nhập `item_id` để tìm sản phẩm tương tự
- Sử dụng Content-Based Filtering (cosine similarity trên embeddings)
- Có nút "Xem tương tự" để liên tục khám phá

### ⭐ Người Dùng Mới (`coldstart.html`)
- **Cold Start **`: Người dùng chưa có lịch sử tương tác
- Nhập danh sách sản phẩm yêu thích + rating
- Nhận gợi ý từ Content-Based System

## Features

✅ **Responsive Design** - Tối ưu cho mobile/tablet/desktop
✅ **Real-time Search** - Fetch API lấy dữ liệu realtime
✅ **Error Handling** - Xử lý lỗi chi tiết
✅ **Loading States** - Spinner khi đang tải
✅ **Bootstrap 5 UI** - Giao diện modern
✅ **CORS Support** - Frontend/Backend chạy trên port khác
✅ **Swagger Docs** - Tài liệu API tự động

## CORS Configuration

Backend đã configure để cho phép CORS từ mọi origin (dev mode).
Để production, cần update:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Chỉnh sửa
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Troubleshooting

### ❌ "Connection refused: localhost:8000"
- Kiểm tra backend có chạy không: `python backend/main.py`
- Kiểm tra port 8000 có bị dùng bởi process khác không

### ❌ "No such file: final_recommendations.parquet"
- Đảm bảo đã chạy đầy đủ Parts 1-4 để sinh dữ liệu
- Kiểm tra path trong `main.py`

### ❌ "Content-based engine not available"
- Files embedding/FAISS chưa được sinh
- Hoặc chưa chạy Part 3 hoàn toàn
- Sẽ dùng fallback (Popular Items) cho Content-Based endpoints

## Performance Notes

- **Popular Items**: ~instant (in-memory)
- **User Recommendations**: ~50-200ms (Parquet filter + ranking)
- **Similar Items**: ~100-500ms (FAISS search + normalization)
- **New User Recs**: ~150-800ms (embedding + attention model nếu load)

## Development Tips

1. **Debug Mode**: Chạy backend với `--reload`
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Test APIs**: Sử dụng Swagger UI (`http://localhost:8000/docs`)

3. **Browser Console**: Để debug JavaScript (F12)

4. **Network Tab**: Xem chi tiết API requests/responses

## Future Enhancements

- [ ] Add authentication/login
- [ ] Save user history to database
- [ ] Real-time model updates
- [ ] A/B testing infrastructure
- [ ] Advanced analytics dashboard
- [ ] Docker containerization
- [ ] Deploy to cloud (AWS/GCP/Azure)

## License

MIT - Xem [LICENSE](../LICENSE) cho chi tiết
