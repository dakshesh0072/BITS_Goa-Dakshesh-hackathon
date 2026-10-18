from functools import lru_cache

from transformers import pipeline


MODEL_NAME = "ProsusAI/finbert"
MINIMUM_CONFIDENCE = 0.55


@lru_cache
def get_finbert_classifier():
    return pipeline(
        "text-classification",
        model=MODEL_NAME,
        tokenizer=MODEL_NAME,
    )


def format_sentiment_prediction(predictions: list[dict]) -> dict:
    if predictions and isinstance(predictions[0], list):
        predictions = predictions[0]

    probabilities = {
        prediction["label"].lower(): round(float(prediction["score"]), 4)
        for prediction in predictions
    }

    positive_probability = probabilities.get("positive", 0.0)
    negative_probability = probabilities.get("negative", 0.0)
    neutral_probability = probabilities.get("neutral", 0.0)

    predicted_label = max(probabilities, key=probabilities.get)
    confidence = probabilities[predicted_label]
    sentiment_score = round(positive_probability - negative_probability, 4)

    if confidence < MINIMUM_CONFIDENCE:
        predicted_label = "neutral"
        sentiment_score = 0.0

    return {
        "label": predicted_label,
        "confidence": round(confidence, 4),
        "probabilities": {
            "positive": positive_probability,
            "negative": negative_probability,
            "neutral": neutral_probability,
        },
        "score": sentiment_score,
    }


def analyze_financial_sentiments(texts: list[str]) -> list[dict]:
    classifier = get_finbert_classifier()
    prediction_batches = classifier(
        texts,
        top_k=None,
        truncation=True,
        max_length=512,
        batch_size=8,
    )

    return [format_sentiment_prediction(predictions) for predictions in prediction_batches]


def analyze_financial_sentiment(text: str) -> dict:
    return analyze_financial_sentiments([text])[0]
