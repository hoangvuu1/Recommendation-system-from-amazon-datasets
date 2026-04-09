from pydantic import BaseModel
from typing import Optional


class ItemMetadata(BaseModel):
    product_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    features: Optional[list] = None


class RecommendationItem(BaseModel):
    rank: int
    item_id: str
    score: float
    metadata: Optional[ItemMetadata] = None


class PopularItemsResponse(BaseModel):
    items: list[RecommendationItem]
    total: int


class UserRecommendationRequest(BaseModel):
    user_id: str
    top_k: int = 10


class UserRecommendationResponse(BaseModel):
    user_id: str
    items: list[RecommendationItem]
    total: int


class SimilarItemsResponse(BaseModel):
    item_id: str
    similar_items: list[RecommendationItem]
    total: int


class NewUserRequest(BaseModel):
    interactions: list[dict]  # [{"item_id": "...", "rating": 5}, ...]
    top_k: int = 10


class NewUserResponse(BaseModel):
    items: list[RecommendationItem]
    total: int
