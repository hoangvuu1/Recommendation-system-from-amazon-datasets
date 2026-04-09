from dataclasses import dataclass

@dataclass(slots=True)
class Interaction:
    item_id: str
    rating: float | int
    timestamp: int | None = None

@dataclass(slots=True)
class UserContext:
    user_id: str
    interactions: list[Interaction]

@dataclass(slots=True)
class RecommendationResult:
    item_id: str
    score: float
    rank: int
