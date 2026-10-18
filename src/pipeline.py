from datetime import datetime, timezone
from src.models import EventType, RiskSignal, TextItem
from src.nlp.finbert_sentiment import analyze_financial_sentiments
from src.nlp.event_classifier import classify_financial_events


EVENT_SEVERITY = {
    EventType.GEOPOLITICAL: 0.95,
    EventType.MACROECONOMIC: 0.85,
    EventType.CREDIT_EVENT: 0.85,
    EventType.MERGER_ACQUISITION: 0.60,
    EventType.EARNINGS: 0.55,
    EventType.REGULATORY: 0.65,
    EventType.MARKET_MOVEMENT: 0.50,
    EventType.PRODUCT_LAUNCH: 0.25,
    EventType.OTHER: 0.20,
}


def calculate_impact(
    sentiment_score: float,
    event_type: EventType,
    sentiment_confidence: float,
    event_confidence: float,
    source: str,
) -> int:
    sentiment_strength = abs(sentiment_score)
    event_severity = EVENT_SEVERITY[event_type]
    combined_confidence = (
        0.60 * sentiment_confidence
        + 0.40 * event_confidence
    )

    raw_impact = (
        1
        + 3.0 * sentiment_strength
        + 4.0 * event_severity
        + 2.0 * combined_confidence
    )

    source_multiplier = 1.0 if source == "news" else 0.85
    impact_score = round(1 + (raw_impact - 1) * source_multiplier)

    return max(1, min(10, impact_score))


def build_risk_signal(
    item: TextItem,
    sentiment_result: dict,
    event_result: dict,
) -> RiskSignal:
    event_type = EventType(event_result["label"])

    impact = calculate_impact(
        sentiment_score=sentiment_result["score"],
        event_type=event_type,
        sentiment_confidence=sentiment_result["confidence"],
        event_confidence=event_result["confidence"],
        source=item.source,
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
        event_confidence=event_result["confidence"],
        impact_score=impact,
        processed_at=datetime.now(timezone.utc),
    )


def analyze_items(items: list[TextItem]) -> list[RiskSignal]:
    if not items:
        return []

    texts = [item.text for item in items]
    sentiment_results = analyze_financial_sentiments(texts)
    event_results = classify_financial_events(texts)

    return [
        build_risk_signal(item, sentiment_result, event_result)
        for item, sentiment_result, event_result in zip(
            items,
            sentiment_results,
            event_results,
        )
    ]


def analyze_text(item: TextItem) -> RiskSignal:
    return analyze_items([item])[0]
