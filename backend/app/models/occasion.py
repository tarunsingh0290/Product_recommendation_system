from dataclasses import dataclass

@dataclass(frozen=True)
class OccasionIntent:
    valid: bool
    occasion: str
    intent_summary: str
    gift_categories: list[str]
    search_phrases: list[str]
    excluded_occasions: list[str]
