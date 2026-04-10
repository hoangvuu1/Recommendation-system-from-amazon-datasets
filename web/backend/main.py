from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from pathlib import Path
import os
import sys

# Add project to path for imports
project_path = Path(__file__).parent.parent.parent
backend_path = Path(__file__).parent
if str(project_path) not in sys.path:
    sys.path.insert(0, str(project_path))
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Content-based engine will be imported on-demand (lazy loading)
ContentBasedEngine = None
EngineConfig = None
Interaction = None
UserContext = None

from schemas import (
    PopularItemsResponse,
    UserRecommendationResponse,
    SimilarItemsResponse,
    NewUserResponse,
    RecommendationItem,
    ItemMetadata,
)
from product_mapper import get_product_mapper

# Initialize FastAPI app
app = FastAPI(
    title="Recommendation System - Amazon Office Products",
    description="Hệ thống gợi ý sản phẩm văn phòng Amazon",
    version="1.0.0"
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in dev mode
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR.parent / "Hybrid"
CONTENT_BASED_ENGINE_PATH = BASE_DIR.parent / "content_based"

# Global variables
final_recommendations_df = None
popular_items_df = None
meta_df = None
content_based_engine = None


def load_content_based_engine():
    """Load content-based engine on-demand (lazy loading)
    
    This is deferred until needed because:
    1. Embeddings and FAISS index are large files (slow to load)
    2. PyTorch/FAISS imports are heavy
    3. Most requests only need hybrid/popular recommendations
    """
    global content_based_engine, ContentBasedEngine, EngineConfig, Interaction, UserContext
    
    if content_based_engine is not None:
        return content_based_engine  # Already loaded
    
    try:
        print("⏳ Loading content-based engine (first request, this may take ~30s)...")
        from content_based.engine import ContentBasedEngine as CBEngine
        from content_based.engine import EngineConfig as CBConfig
        from content_based.engine import Interaction as CBInteraction
        from content_based.engine import UserContext as CBUserContext
        
        ContentBasedEngine = CBEngine
        EngineConfig = CBConfig
        Interaction = CBInteraction
        UserContext = CBUserContext
        
        engine_dir = CONTENT_BASED_ENGINE_PATH / "engine" / "embedding_matrix"
        faiss_dir = CONTENT_BASED_ENGINE_PATH / "engine" / "faiss"
        
        if engine_dir.exists() and faiss_dir.exists():
            config = EngineConfig(
                top_k=100,
                negative_lambda=0.3,
                attention_mix_alpha=0.5,
                exclude_history_items=True,
            )
            
            content_based_engine = ContentBasedEngine.from_files(
                embedding_path=str(engine_dir / "embeddings.npy"),
                id2idx_path=str(engine_dir / "id2idx.pkl"),
                faiss_index_path=str(faiss_dir / "products_hnsw.index"),
                faiss_ids_path=str(faiss_dir / "products_ids.pkl"),
                config=config,
                attention_checkpoint_path=None,
            )
            print("✓ Content-based engine loaded successfully")
            return content_based_engine
        else:
            print("⚠ Content-based engine files not found")
            return None
    except Exception as e:
        print(f"❌ Failed to load content-based engine: {e}")
        return None


def load_data():
    """Load all recommendation data and metadata (fast path)
    
    Loads hybrid recommendations and metadata immediately.
    Content-based engine is loaded on-demand to avoid startup delay.
    """
    global final_recommendations_df, popular_items_df, meta_df, product_mapper
    
    try:
        # Load parquet files (fast - < 2 seconds)
        final_recommendations_df = pd.read_parquet(DATA_DIR / "final_recommendations.parquet")
        popular_items_df = pd.read_parquet(DATA_DIR / "popular_items.parquet")
        
        print("[OK] Loaded final_recommendations.parquet (3.3M rows)")
        print("[OK] Loaded popular_items.parquet (100 items)")
        
        # Load product names from cache (fast!)
        product_mapper = get_product_mapper()
        try:
            cache_file = BASE_DIR.parent / "product_names_cache.pkl"
            if cache_file.exists():
                product_mapper.load_from_cache(str(cache_file))
                print(f"[OK] Loaded product names from cache")
            else:
                print(f"[WARN] Cache file not found, will try parquet files")
                meta_ui_path = BASE_DIR.parent / "meta_ui"
                product_mapper.load_from_parquet(str(meta_ui_path))
        except Exception as e:
            print(f"[WARN] Failed to load product names: {e}")
        
        # Try to load metadata if available
        try:
            meta_df = pd.read_parquet(BASE_DIR.parent / "RS-20260405T032136Z-1-001" / "RS" / "meta_rs.parquet")
            print("[OK] Loaded meta_rs.parquet")
        except:
            meta_df = None
            print("[WARN] meta_rs.parquet not found - using product names from meta_ui")
        
        # Content-based engine will be loaded on-demand
        print("[OK] Content-based engine will be loaded on first request (lazy loading)")
    
    except Exception as e:
        print(f"[ERROR] Error loading data: {e}")
        raise


def get_item_metadata(item_id: str) -> ItemMetadata:
    """Get metadata for an item (title, image, description) from product mapper"""
    global product_mapper, meta_df
    metadata = ItemMetadata(product_id=item_id)
    
    # First, try to get from product_mapper (meta_ui parquet files with images)
    if product_mapper is not None:
        product_info = product_mapper.get_product_info(item_id)
        if product_info.get('title'):
            metadata.title = product_info.get('title')
            metadata.image_url = product_info.get('image_url')
            
            # Try to get description from meta_df if available
            if meta_df is not None and item_id in meta_df['product_id'].values:
                item = meta_df[meta_df['product_id'] == item_id].iloc[0]
                metadata.description = str(item.get('description', '')) if pd.notna(item.get('description')) else None
                try:
                    features = item.get('features')
                    if features and pd.notna(features):
                        if isinstance(features, str):
                            metadata.features = eval(features)
                        else:
                            metadata.features = features
                except:
                    pass
            return metadata
    
    # Fall back to meta_df if available
    if meta_df is not None and item_id in meta_df['product_id'].values:
        item = meta_df[meta_df['product_id'] == item_id].iloc[0]
        metadata.title = str(item.get('title', '')) if pd.notna(item.get('title')) else None
        metadata.description = str(item.get('description', '')) if pd.notna(item.get('description')) else None
        
        try:
            features = item.get('features')
            if features and pd.notna(features):
                if isinstance(features, str):
                    metadata.features = eval(features)  # or json.loads if stored as JSON
                else:
                    metadata.features = features
        except:
            pass
    
    return metadata


def format_recommendations(items: list[tuple[str, float]], max_results: int = None) -> list[RecommendationItem]:
    """Format recommendation tuples into RecommendationItem objects, filtering unavailable products"""
    unavailable_text = "Sản phẩm hiện không còn bày bán"
    results = []
    rank = 1
    
    for item_id, score in items:
        if max_results and len(results) >= max_results:
            break
        
        metadata = get_item_metadata(item_id)
        
        # Skip unavailable products
        if metadata.title == unavailable_text:
            continue
        
        rec_item = RecommendationItem(
            rank=rank,
            item_id=item_id,
            score=float(score),
            metadata=metadata
        )
        results.append(rec_item)
        rank += 1
    
    return results


@app.on_event("startup")
async def startup_event():
    """Load data on startup"""
    load_data()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "final_recommendations_loaded": final_recommendations_df is not None,
        "popular_items_loaded": popular_items_df is not None,
        "metadata_loaded": meta_df is not None,
        "content_based_engine_loaded": content_based_engine is not None,
        "note": "Content-based engine loads on-demand (lazy loading)"
    }


@app.get("/recommend/popular", response_model=PopularItemsResponse)
async def get_popular_items(top_k: int = 20):
    """Get popular items for homepage (excluding products not available)"""
    if popular_items_df is None:
        raise HTTPException(status_code=503, detail="Popular items data not loaded")
    
    top_k = min(top_k, 100)
    
    # Placeholder for unavailable products
    unavailable_text = "Sản phẩm hiện không còn bày bán"
    
    recommendations = []
    rank = 1
    
    # Need to fetch more items than top_k because we filter out unavailable ones
    # Fetch up to 3x top_k to ensure we get enough valid products
    max_fetch = min(len(popular_items_df), top_k * 3)
    items = popular_items_df.head(max_fetch)
    
    for row in items.itertuples():
        if len(recommendations) >= top_k:
            break
        
        item_id = row.product_id if hasattr(row, 'product_id') else row[0]
        score = row.score if hasattr(row, 'score') else row[1]
        
        # Get metadata to check if product is available
        metadata = get_item_metadata(item_id)
        
        # Skip unavailable products
        if metadata.title == unavailable_text:
            continue
        
        recommendations.append(RecommendationItem(
            rank=rank,
            item_id=item_id,
            score=float(score),
            metadata=metadata
        ))
        rank += 1
    
    return PopularItemsResponse(items=recommendations, total=len(recommendations))


@app.get("/recommend/user/{user_id}", response_model=UserRecommendationResponse)
async def get_user_recommendations(user_id: str, top_k: int = 10):
    """Get recommendations for a specific user (Hybrid system, excluding unavailable products)"""
    if final_recommendations_df is None:
        raise HTTPException(status_code=503, detail="Recommendations data not loaded")
    
    top_k = min(top_k, 100)
    unavailable_text = "Sản phẩm hiện không còn bày bán"
    
    # Filter recommendations for this user and get top-k
    user_recs = final_recommendations_df[
        final_recommendations_df['user_id'] == user_id
    ].nlargest(top_k * 3, 'final_score')  # Fetch more to filter out unavailable
    
    if user_recs.empty:
        # If user not found in hybrid recommendations, suggest popular items
        return UserRecommendationResponse(
            user_id=user_id,
            items=format_recommendations([(row.product_id, row.score) 
                                         for row in popular_items_df.head(top_k * 3).itertuples()], top_k),
            total=0
        )
    
    recommendations = []
    rank = 1
    
    for row in user_recs.itertuples():
        if len(recommendations) >= top_k:
            break
        
        metadata = get_item_metadata(row.product_id)
        
        # Skip unavailable products
        if metadata.title == unavailable_text:
            continue
        
        recommendations.append(RecommendationItem(
            rank=rank,
            item_id=row.product_id,
            score=float(row.final_score),
            metadata=metadata
        ))
        rank += 1
    
    return UserRecommendationResponse(
        user_id=user_id,
        items=recommendations,
        total=len(recommendations)
    )


@app.get("/recommend/item/{item_id}", response_model=SimilarItemsResponse)
async def get_similar_items(item_id: str, top_k: int = 10):
    """Get similar items using content-based filtering"""
    # Load engine on-demand
    engine = load_content_based_engine()
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="Content-based engine not available. Try using /recommend/popular instead."
        )
    
    if Interaction is None or UserContext is None:
        raise HTTPException(
            status_code=503,
            detail="Content-based engine dependencies not available."
        )
    
    top_k = min(top_k, 100)
    
    # Create a dummy user context with only this item rated highly
    interactions = [Interaction(item_id=item_id, rating=5)]
    user_context = UserContext(user_id=f"temp_{item_id}", interactions=interactions)
    
    try:
        similar_items = engine.recommend(
            user_context,
            algorithm="weighted_avg",
            top_k=top_k
        )
        
        recommendations = []
        for rec in similar_items:
            metadata = get_item_metadata(rec.item_id)
            
            # Skip unavailable products
            if metadata.title == "Sản phẩm hiện không còn bày bán":
                continue
            
            recommendations.append(RecommendationItem(
                rank=len(recommendations) + 1,
                item_id=rec.item_id,
                score=rec.score,
                metadata=metadata
            ))
            
            # Stop when we have enough valid recommendations
            if len(recommendations) >= top_k:
                break
        
        return SimilarItemsResponse(
            item_id=item_id,
            similar_items=recommendations,
            total=len(recommendations)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error getting similar items: {str(e)}")


@app.post("/recommend/new-user", response_model=NewUserResponse)
async def get_new_user_recommendations(interactions: list[dict], top_k: int = 10):
    """Get recommendations for a new user (Cold Start) using content-based filtering
    
    interactions: [{"item_id": "...", "rating": 5}, ...]
    """
    # Load engine on-demand
    engine = load_content_based_engine()
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="Content-based engine not available for new user recommendations"
        )
    
    if Interaction is None or UserContext is None:
        raise HTTPException(
            status_code=503,
            detail="Content-based engine dependencies not available."
        )
    
    if not interactions:
        # No interactions, return popular items (excluding unavailable ones)
        popular = popular_items_df.head(top_k * 3)
        return NewUserResponse(
            items=format_recommendations([(row.product_id, row.score) 
                                         for row in popular.itertuples()], top_k),
            total=0  # User had no interactions
        )
    
    top_k = min(top_k, 100)
    
    # Convert interactions to Interaction objects
    interaction_objs = [
        Interaction(item_id=item["item_id"], rating=item.get("rating", 5))
        for item in interactions
    ]
    
    user_context = UserContext(user_id="new_user", interactions=interaction_objs)
    
    try:
        recommendations = engine.recommend(
            user_context,
            algorithm="weighted_avg",
            top_k=top_k * 3  # Fetch more to filter unavailable ones
        )
        
        rec_items = []
        rank = 1
        
        for rec in recommendations:
            if len(rec_items) >= top_k:
                break
            
            metadata = get_item_metadata(rec.item_id)
            
            # Skip unavailable products
            if metadata.title == "Sản phẩm hiện không còn bày bán":
                continue
            
            rec_items.append(RecommendationItem(
                rank=rank,
                item_id=rec.item_id,
                score=rec.score,
                metadata=metadata
            ))
            rank += 1
        
        return NewUserResponse(items=rec_items, total=len(rec_items))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error generating recommendations: {str(e)}")


@app.get("/metadata/{item_id}", response_model=ItemMetadata)
async def get_metadata(item_id: str):
    """Get metadata for a specific item"""
    return get_item_metadata(item_id)


# Mount static files (CSS, JS, images)
frontend_path = BASE_DIR / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


@app.get("/")
async def root():
    """Serve homepage"""
    frontend_path = BASE_DIR / "frontend"
    index_file = frontend_path / "index.html"
    
    if index_file.exists():
        return FileResponse(str(index_file), media_type="text/html")
    
    return {"message": "Welcome to Recommendation System API", "docs": "/docs"}


@app.get("/recommend.html")
async def recommend_page():
    """Serve user recommendations page"""
    frontend_path = BASE_DIR / "frontend"
    file = frontend_path / "recommend.html"
    
    if file.exists():
        return FileResponse(str(file), media_type="text/html")
    
    raise HTTPException(status_code=404, detail="Page not found")


@app.get("/similar.html")
async def similar_page():
    """Serve similar items page"""
    frontend_path = BASE_DIR / "frontend"
    file = frontend_path / "similar.html"
    
    if file.exists():
        return FileResponse(str(file), media_type="text/html")
    
    raise HTTPException(status_code=404, detail="Page not found")


@app.get("/coldstart.html")
async def coldstart_page():
    """Serve cold start page"""
    frontend_path = BASE_DIR / "frontend"
    file = frontend_path / "coldstart.html"
    
    if file.exists():
        return FileResponse(str(file), media_type="text/html")
    
    raise HTTPException(status_code=404, detail="Page not found")


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Recommendation System API")
    print("📚 Documentation: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
