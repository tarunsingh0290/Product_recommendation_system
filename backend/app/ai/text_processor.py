from app.models.occasion import OccasionIntent

def query_text(context: OccasionIntent) -> str:
    return ' '.join([context.occasion, context.intent_summary,
                     *context.gift_categories, *context.search_phrases])
