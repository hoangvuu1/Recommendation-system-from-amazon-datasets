from dataclasses import dataclass

@dataclass(slots=True)
class EngineConfig:
    top_k: int = 100
    max_context: int = 50

    positive_threshold: float = 4.0
    negative_threshold: float = 2.0
    neutral_promote_threshold: int = 3
    min_positive_items: int = 2

    negative_lambda: float = 0.3
    attention_mix_alpha: float = 0.5

    fallback_strategy: str = "mean"   # "mean" | "random"
    random_seed: int = 42

    exclude_history_items: bool = True
