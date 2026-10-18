from functools import lru_cache

from transformers import pipeline


MODEL_NAME = "facebook/bart-large-mnli"
MINIMUM_CONFIDENCE = 0.40

EVENT_LABELS = [
    "Geopolitical",
    "Macroeconomic",
    "Credit Event",
    "Merger/Acquisition",
    "Earnings",
    "Product Launch",
    "Regulatory",
    "Market Movement",
    "Other",
]


@lru_cache
def get_event_classifier():
    return pipeline(
        "zero-shot-classification",
        model=MODEL_NAME,
    )


def format_event_prediction(result: dict) -> dict:
    label = result["labels"][0]
    confidence = round(float(result["scores"][0]), 4)

    if confidence < MINIMUM_CONFIDENCE:
        label = "Other"

    return {
        "label": label,
        "confidence": confidence,
    }


def classify_financial_events(texts: list[str]) -> list[dict]:
    classifier = get_event_classifier()

    results = classifier(
        texts,
        candidate_labels=EVENT_LABELS,
        multi_label=False,
        truncation=True,
        max_length=512,
        batch_size=4,
    )

    return [format_event_prediction(result) for result in results]



def classify_financial_event(text: str) -> dict:
    return classify_financial_events([text])[0]
