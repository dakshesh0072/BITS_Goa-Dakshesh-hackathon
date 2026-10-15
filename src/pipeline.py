from datetime import datetime, timezone
from src.models import EventType, RiskSignal, TextItem


EVENT_KEYWORDS = {
    EventType.GEOPOLITICAL: ["war", "sanction", "tariff", "conflict"],
    EventType.MACROECONOMIC: ["inflation", "interest rate", "gdp", "recession"],
    EventType.CREDIT_EVENT: ["default", "downgrade", "debt", "bankruptcy"],
    EventType.MERGER_ACQUISITION: ["merger", "acquisition", "takeover"],
    EventType.EARNINGS: ["earnings", "revenue", "guidance", "profit"],
    EventType.PRODUCT_LAUNCH: ["launch", "unveils", "new product"],
    EventType.REGULATORY: ["regulator", "antitrust", "fine", "ban"],
}

POSITIVE_WORDS = ["beat", "growth", "surge", "profit", "strong", "record", "approval"]
NEGATIVE_WORDS = ["fall", "drop", "loss", "weak", "miss", "risk", "lawsuit", "default"]


def classify_event(text: str) -> EventType:
    text_lower = text.lower()

    for event_type, keywords in EVENT_KEYWORDS.items():
        if any(word in text_lower for word in keywords):
            return event_type

    return EventType.OTHER


def calculate_sentiment(text: str) -> float:
    text_lower = text.lower()
    positive_count = sum(word in text_lower for word in POSITIVE_WORDS)
    negative_count = sum(word in text_lower for word in NEGATIVE_WORDS)
    total = positive_count + negative_count

    if total == 0:
        return 0.0

    return round((positive_count - negative_count) / total, 2)


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
    event_type = classify_event(item.text)
    sentiment = calculate_sentiment(item.text)
    impact = calculate_impact(sentiment, event_type)

    return RiskSignal(
        source=item.source,
        text=item.text,
        company=item.company,
        sentiment_score=sentiment,
        event_classification=event_type,
        impact_score=impact,
        processed_at=datetime.now(timezone.utc),
    )