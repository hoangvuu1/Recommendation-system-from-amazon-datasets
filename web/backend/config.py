"""
Configuration for Recommendation System API
"""

from dataclasses import dataclass
from pathlib import Path

# === Backend Server Config ===
API_HOST = "0.0.0.0"
API_PORT = 8000
API_WORKERS = 1
DEBUG = True
RELOAD = True

# === Data Paths (Relative to web/ directory) ===
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "Hybrid"
CONTENT_BASED_ENGINE_PATH = BASE_DIR / "content_based"

# Parquet files
FINAL_RECOMMENDATIONS_PATH = DATA_DIR / "final_recommendations.parquet"
POPULAR_ITEMS_PATH = DATA_DIR / "popular_items.parquet"
METADATA_PATH = BASE_DIR / "RS-20260405T032136Z-1-001" / "RS" / "meta_rs.parquet"

# Content-Based Engine files
EMBEDDINGS_PATH = CONTENT_BASED_ENGINE_PATH / "engine" / "embedding_matrix" / "embeddings.npy"
ID2IDX_PATH = CONTENT_BASED_ENGINE_PATH / "engine" / "embedding_matrix" / "id2idx.pkl"
FAISS_INDEX_PATH = CONTENT_BASED_ENGINE_PATH / "engine" / "faiss" / "products_hnsw.index"
FAISS_IDS_PATH = CONTENT_BASED_ENGINE_PATH / "engine" / "faiss" / "products_ids.pkl"
ATTENTION_MODEL_PATH = CONTENT_BASED_ENGINE_PATH / "engine" / "attention_profile_model.pth"

# === API Response Config ===
MAX_TOP_K = 100
DEFAULT_TOP_K = 10

# === Content-Based Engine Config ===
@dataclass
class ContentBasedEngineConfig:
    top_k: int = 100
    max_context: int = 50
    positive_threshold: float = 4.0
    negative_threshold: float = 2.0
    negative_lambda: float = 0.3
    attention_mix_alpha: float = 0.5
    fallback_strategy: str = "mean"
    exclude_history_items: bool = True

# === CORS Config ===
CORS_ORIGINS = ["*"]  # Allow all origins for dev, restrict in production
CORS_CREDENTIALS = True
CORS_METHODS = ["*"]
CORS_HEADERS = ["*"]

# === Logging ===
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
