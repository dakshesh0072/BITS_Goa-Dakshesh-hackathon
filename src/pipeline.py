from datetime import datetime, timezone
from src.models import EventType, RiskSignal, TextItem
from src.nlp.finbert_sentiment import analyze_financial_sentiment

EVENT_KEYWORDS = {
    EventType.GEOPOLITICAL: ["war", "sanction", "tariff", "conflict"],
    EventType.MACROECONOMIC: ["inflation", "interest rate", "gdp", "recession"],
    EventType.CREDIT_EVENT: ["default", "downgrade", "debt", "bankruptcy"],
    EventType.MERGER_ACQUISITION: ["merger", "acquisition", "takeover"],
    EventType.EARNINGS: ["earnings", "revenue", "guidance", "profit"],
    EventType.PRODUCT_LAUNCH: ["launch", "unveils", "new product"],
    EventType.REGULATORY: ["regulator", "antitrust", "fine", "ban"],
}



def classify_event(text: str) -> EventType:
    text_lower = text.lower()

    for event_type, keywords in EVENT_KEYWORDS.items():
        if any(word in text_lower for word in keywords):
            return event_type

    return EventType.OTHER




def calculate_impact(sentiment: float, event_type: EventType) -> int:
    impact = 2 + round(abs(sentiment) * 4)

    if event_type in [
        EventType.GEOPOLITICAL,
        EventType.MACROECONOMIC,
        EventType.CREDIT_EVENT,
    ]:
        impact += 3

    return min(impact, 10)


def analyze_text(item: TextItem) -> RiskSignal:
    sentiment_result = analyze_financial_sentiment(item.text)
    event_type = classify_event(item.text)

    impact = calculate_impact(
        sentiment_result["score"],
        event_type,
    )

    return RiskSignal(
        source=item.source,
        text=item.text,
        company=item.company,
        sentiment_score=sentiment_result["score"],
        sentiment_label=sentiment_result["label"],
        sentiment_confidence=sentiment_result["confidence"],
        sentiment_probabilities=sentiment_result["probabilities"],
        event_classification=event_type,
        impact_score=impact,
        processed_at=datetime.now(timezone.utc),
    )