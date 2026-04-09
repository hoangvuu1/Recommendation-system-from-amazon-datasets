# Recommendation System – Amazon Office Products

Dự án môn học **Hệ Gợi Ý (Recommender Systems)** – xây dựng hệ thống gợi ý sản phẩm văn phòng từ bộ dữ liệu Amazon Reviews 2023.

---

## Tổng quan hệ thống

```
Raw Data (Amazon Office Products)
        │
        ▼
┌─────────────────────┐
│  Part 1: Tiền xử lý │  → rating_rs.parquet
│  (Preprocessing)    │  → meta_rs.parquet
│                     │  → item_embedding.parquet (SBERT)
└─────────────────────┘
        │
        ├──────────────────────────┐
        ▼                          ▼
┌─────────────────────┐  ┌────────────────────────────┐
│  Part 2: ALS (CF)   │  │  Part 3: Content-based     |
│  + Evaluation       │  │                            │
└─────────────────────┘  └────────────────────────────┘
        │                          │
        └──────────┬───────────────┘
                   ▼
        ┌─────────────────────┐
        │  Part 4: Hybrid     │
        │  + Cold Start Logic │
        └─────────────────────┘
                   │
                   ▼
        ┌─────────────────────────────┐
        │  Part 5: Web Demo           │
        │  (FastAPI + HTML/JS) ✅     │
        └─────────────────────────────┘
```

---

## Dataset

**Nguồn**: [Amazon Reviews 2023](https://amazon-reviews-2023.github.io/) – danh mục **Office Products**

| File | Kích thước | Mô tả |
|---|---|---|
| `Office_Products.jsonl` | ~5.4 GB | 12.8M reviews của người dùng |
| `meta_Office_Products.jsonl` | ~2 GB | Thông tin 710K sản phẩm |

**Thống kê chính:**

| Chỉ số | Giá trị |
|---|---|
| Tổng số reviews (raw) | 12,845,712 |
| Tổng số users (raw) | 7,613,158 |
| Tổng số sản phẩm (raw) | 906,049 |
| Reviews sau khi lọc (≥5 ratings/user, ≥5 ratings/item) | 2,165,547 |
| Thời gian dữ liệu | 1998 – 2023 |
| Rating trung bình | 4.21 / 5.0 |

---

## Cấu trúc thư mục

```
Recommendation-system-from-amazon-datasets/
│
├── notebook/                        # EDA notebooks
│   ├── data_exploration_1.ipynb     # User analysis (review count, rating distribution)
│   ├── data_exploration_2.ipynb     # Item analysis (reviews/item, top items)
│   ├── data_exploration_3.ipynb     # Text & temporal analysis
│   └── data_exploration_4.ipynb     # Rating statistics, long tail distribution
│
├── recommender/                     # Model notebooks
│   ├── preprocessing.ipynb          # Part 1: Tiền xử lý dữ liệu
│   ├── collaborative_filtering.ipynb # Part 2: ALS + Evaluation  (TODO)
│   ├── content_based.ipynb          # Part 3: Content-based      (TODO)
│   ├── hybrid.ipynb                 # Part 4: Hybrid System      (TODO)
│   └── web/                         # Part 5: Demo Web           (TODO)
│
├── RS-20260405T032136Z-1-001/RS/    # Processed data (Google Drive export)
│   ├── rating_rs.parquet
│   ├── meta_rs.parquet
│   └── feature_meta_Sbert/
│       └── item_embedding.parquet
│
├── plan.md                          # Kế hoạch triển khai Part 2
├── phân-chia-cv.docx                # Tài liệu phân chia công việc
└── README.md
```

---

## Phân chia công việc

### Part 1 – Data Preprocessing

**Mục tiêu**: Tạo dataset sạch cho các mô hình downstream.

**Các bước thực hiện:**
- Load review data (12.8M rows) và meta data (710K items)
- Chọn các cột cần thiết, xóa null
- Lọc users có ≥ 5 ratings, items có ≥ 5 ratings
- Rename columns (asin → product_id, rating → review_rating, ...)
- Làm sạch text meta (lowercase, xóa tiếng Trung, xóa ký tự đặc biệt)
- Tạo item embedding bằng SBERT (`all-MiniLM-L6-v2`, 384 chiều)

**Output:**

| File | Columns |
|---|---|
| `rating_rs.parquet` | user_id, product_id, product_parent, review_rating, review_date, verified_purchase |
| `meta_rs.parquet` | product_id, title, description, features |
| `item_embedding.parquet` | product_id, embedding (list[float], 384-dim) |

---

### Part 2 – Collaborative Filtering (ALS) + Evaluation

**Mục tiêu**: Xây dựng mô hình học từ hành vi người dùng và đánh giá toàn bộ hệ thống.

**Kỹ thuật**: Spark MLlib `ALS` (Alternating Least Squares)

**Các bước thực hiện:**
- Load `rating_rs.parquet`
- StringIndexer: `user_id` → `user_idx`, `product_id` → `item_idx`
- Train/Test split: 80/20 (random seed = 42)
- Hyperparameter tuning: rank ∈ {10, 20, 50}, regParam ∈ {0.01, 0.1}, maxIter ∈ {10, 20}
- Generate Top-10 recommendations cho tất cả users
- Đánh giá đầy đủ (xem bên dưới)

**ALS Configuration:**
```python
ALS(
    userCol="user_idx",
    itemCol="item_idx",
    ratingCol="review_rating",
    coldStartStrategy="drop",
    nonnegative=True
)
```

**Evaluation (gộp từ Part 5):**

| Model | Metric | Mô tả |
|---|---|---|
| ALS | RMSE | Rating prediction accuracy |
| ALS | Precision@10 | Tỉ lệ item gợi ý đúng trong top-10 |
| ALS | Recall@10 | Độ phủ item relevant trong top-10 |
| ALS | NDCG@10 | Ranking quality (có tính vị trí) |
| Content-based | Precision@10 | Đánh giá sau khi Part 3 hoàn thành |
| Hybrid | Precision@10, Recall@10 | Đánh giá sau khi Part 4 hoàn thành |

> Ground truth cho ranking metrics: items user đánh giá ≥ 4 sao trong test set.

**Output:**

| File | Columns |
|---|---|
| `als_recommendations.parquet` | user_id, product_id, als_score |
| `als_model/` | Saved Spark ALS model |
| `user_indexer_labels.parquet` | user_idx ↔ user_id mapping |
| `item_indexer_labels.parquet` | item_idx ↔ product_id mapping |

---

### Part 3 – Content-based Filtering

**Mục tiêu**: Gợi ý dựa trên nội dung sản phẩm, xử lý Cold Start.

**Kỹ thuật**: Cosine Similarity trên SBERT embeddings (đã có từ Part 1)

**Các bước thực hiện:**
- Load `item_embedding.parquet`
- Tính cosine similarity giữa các cặp items
- Với mỗi item → lưu top-K items tương tự nhất

**Output:**

| File | Columns |
|---|---|
| `item_similarity.parquet` | item_id, similar_item_id, similarity_score |

---

### Part 4 – Hybrid System + Cold Start Logic

**Mục tiêu**: Kết hợp ALS và Content-based, xử lý mọi trường hợp người dùng.

**Logic hệ thống:**

```
User có lịch sử  →  Hybrid: 0.7 × ALS + 0.3 × Content-based
User mới         →  Content-based (theo category yêu thích)
Item mới         →  Content-based
Không có gì      →  Popular Items (top rating count)
```

**Công thức Hybrid:**
```
Final Score = 0.7 × normalize(ALS_score) + 0.3 × normalize(Content_score)
```

**Output:**

| File | Columns |
|---|---|
| `final_recommendations.parquet` | user_id, product_id, final_score |
| `popular_items.parquet` | product_id, score (cho cold start) |

---

### Part 5 – Demo Web

**Mục tiêu**: Giao diện trực quan để demo toàn bộ hệ thống.

**Tech stack**: FastAPI (backend) + HTML/JS hoặc React (frontend)

**Các trang:**

| Trang | Chức năng | API |
|---|---|---|
| Trang chủ | Hiển thị Popular Products | `GET /recommend/popular` |
| Recommend for User | Nhập user_id → Top-N (Hybrid) | `GET /recommend/user/{user_id}` |
| Similar Products | Nhập item_id → Sản phẩm tương tự | `GET /recommend/item/{item_id}` |
| Cold Start | Chọn category → Gợi ý theo nội dung | `POST /recommend/new-user` |

---

### Part 5 – Demo Web ✅ HOÀN THÀNH

**Mục tiêu**: Giao diện trực quan để demo toàn bộ hệ thống.

**Tech stack**: FastAPI (backend) + HTML/JS (frontend)

**Các bước thực hiện:**
- Build FastAPI server với 6 endpoints
- Load dữ liệu từ Parts 1-4 (parquet files)
- Tích hợp content-based engine để tìm sản phẩm tương tự
- Xây dựng 4 trang HTML interactive với Bootstrap 5
- Implement CORS middleware cho frontend-backend communication
- Tạo responsive CSS design cho mobile/tablet/desktop

**API Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/recommend/popular` | GET | Hiển thị sản phẩm phổ biến |
| `/recommend/user/{user_id}` | GET | Gợi ý cho người dùng (Hybrid) |
| `/recommend/item/{item_id}` | GET | Sản phẩm tương tự (Content-based) |
| `/recommend/new-user` | POST | Gợi ý cho người dùng mới (Cold Start) |
| `/metadata/{item_id}` | GET | Lấy thông tin sản phẩm |

**Frontend Pages:**

| Trang | File | Chức năng |
|-------|------|---------|
| Homepage | `index.html` | Hiển thị Top 20 popular products |
| User Recs | `recommend.html` | Nhập user_id → Top-15 recommendations (Hybrid) |
| Similar | `similar.html` | Nhập item_id → Top-15 similar products |
| Cold Start | `coldstart.html` | Thêm interactions → Recommendations (Content-based) |

**Key Features:**
- ✅ Responsive design (Bootstrap 5)
- ✅ Real-time API requests (Fetch API)
- ✅ Error handling & loading states
- ✅ URL parameters support (e.g., `?user_id=ABC`)
- ✅ Product metadata display
- ✅ Navigation between pages
- ✅ Interactive Swagger UI (`/docs`)

**Output:**
- Functional web application serving all parts
- Backend API on `http://localhost:8000`
- Frontend accessible via browser
- Complete documentation & deployment guides

**Files Generated:**
```
web/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── schemas.py           # Pydantic data models
│   ├── config.py            # Configuration management
│   ├── requirements.txt      # Python dependencies
│   └── __init__.py
├── frontend/
│   ├── index.html           # Homepage
│   ├── recommend.html       # User recommendations
│   ├── similar.html         # Similar products
│   ├── coldstart.html       # New user (cold start)
│   └── style.css            # Global styles
├── run.py                   # Python runner script
├── run.bat                  # Windows batch script
├── run.sh                   # Linux/Mac bash script
├── README.md                # Complete web documentation
├── API_TESTING.md           # cURL & Python API examples
├── DEPLOYMENT.md            # Production deployment guide
├── STRUCTURE.md             # Architecture documentation
├── STATUS.md                # Completion status
└── .env.example             # Environment variables
```

**Quick Start:**
```bash
cd web
pip install -r backend/requirements.txt
python run.py
# Open http://localhost:8000
```

**Deployment Options:**
- 🐍 Python script: `python run.py`
- 🪟 Windows batch: `run.bat`
- 🐧 Linux/Mac bash: `bash run.sh`
- 🐳 Docker: `docker-compose up`
- ☁️ Cloud (AWS/GCP/Azure): See `DEPLOYMENT.md`

---

## Kết quả dự kiến

| Model | RMSE | Precision@10 | Recall@10 | NDCG@10 |
|---|---|---|---|---|
| ALS (rank=50, regParam=0.1, maxIter=10) | 1.1921 | 0.0006 | 0.0044 | 0.0041 |
| Content-based | – | ~ | ~ | ~ |
| Hybrid | – | ~ | ~ | ~ |

> Content-based và Hybrid sẽ được cập nhật sau khi Parts 3 và 4 hoàn thành.


## Nhóm thực hiện

| Thành viên | Phần phụ trách | Status |
|---|---|---|
| Nguyễn Thế Hùng | Part 1 – Data Preprocessing | ✅ |
| Thân Tiến Đạt | Part 2 – Collaborative Filtering + Evaluation | ✅ |
| Trần Thế Hưng | Part 3 – Content-based Filtering | ✅ |
| Nguyễn Trung Kiên | Part 4 – Hybrid System + Cold Start | ✅ |
| Vũ Huy Hoàng | Part 5 – Demo Web | ✅ **COMPLETE** |

---

## Quick Links

- 📚 [Web Demo Documentation](web/README.md) - Complete guide for Part 5
- 🚀 [Quick Start Guide](QUICKSTART.md) - 5-minute setup
- 🧪 [API Testing Examples](web/API_TESTING.md) - cURL, Python, Swagger
- 📋 [Deployment Guide](web/DEPLOYMENT.md) - Production setup
- 🏗️ [Architecture Overview](web/STRUCTURE.md) - System design
- ✅ [Part 5 Status](web/STATUS.md) - Completion checklist
