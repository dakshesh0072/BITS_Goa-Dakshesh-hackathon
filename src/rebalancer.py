from datetime import datetime, timedelta, timezone
from pathlib import Path
import json

import pandas as pd

from src.models import RiskSignal


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STOCKS_FILE = PROJECT_ROOT / "data" / "raw" / "stocks.csv"
HISTORY_FILE = PROJECT_ROOT / "data" / "processed" / "rebalance_history.json"


def load_rebalance_history() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []

    return json.loads(HISTORY_FILE.read_text())


def create_initial_snapshot(timestamp: datetime | None = None) -> dict:
    stocks = pd.read_csv(STOCKS_FILE)
    timestamp = timestamp or datetime.now(timezone.utc)

    return {
        "snapshot_type": "initial",
        "rebalanced_at": timestamp.isoformat(),
        "stocks": [
            {
                "ticker": stock["ticker"],
                "initial_weight": round(float(stock["base_weight"]) * 100, 2),
                "previous_weight": round(float(stock["base_weight"]) * 100, 2),
                "sentiment_score": 0.0,
                "new_weight": round(float(stock["base_weight"]) * 100, 2),
            }
            for _, stock in stocks.iterrows()
        ],
    }


def reset_rebalance_history() -> dict:
    """Reset the simulated portfolio and retain only its 10% starting state."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    initial_snapshot = create_initial_snapshot()
    HISTORY_FILE.write_text(json.dumps([initial_snapshot], indent=2))
    return initial_snapshot


def load_current_weights(stocks: pd.DataFrame) -> dict[str, float]:
    """Use the latest rebalance as the next rebalance's starting portfolio."""
    default_weights = {
        stock["ticker"]: float(stock["base_weight"])
        for _, stock in stocks.iterrows()
    }

    history = load_rebalance_history()
    if not history:
        return default_weights

    latest_snapshot = history[-1]
    latest_weights = {
        stock["ticker"]: float(stock["new_weight"]) / 100
        for stock in latest_snapshot["stocks"]
    }

    return {
        ticker: latest_weights.get(ticker, default_weight)
        for ticker, default_weight in default_weights.items()
    }


def rebalance_index(signals: list[RiskSignal]) -> dict:
    stocks = pd.read_csv(STOCKS_FILE)
    current_weights = load_current_weights(stocks)
    rebalanced_stocks = []

    for _, stock in stocks.iterrows():
        ticker = stock["ticker"]
        initial_weight = float(stock["base_weight"])
        previous_weight = current_weights[ticker]

        relevant_signals = [
            signal
            for signal in signals
            if signal.company == ticker and signal.impact_score >= 4
        ]

        if relevant_signals:
            average_sentiment = sum(
                signal.sentiment_score for signal in relevant_signals
            ) / len(relevant_signals)
        else:
            average_sentiment = 0.0

        adjusted_weight = previous_weight * (1 + 0.10 * average_sentiment)
        adjusted_weight = max(0.03, min(0.18, adjusted_weight))

        rebalanced_stocks.append(
            {
                "ticker": ticker,
                "initial_weight": round(initial_weight * 100, 2),
                "previous_weight": round(previous_weight * 100, 2),
                "sentiment_score": round(average_sentiment, 2),
                "new_weight": adjusted_weight,
            }
        )

    total_weight = sum(stock["new_weight"] for stock in rebalanced_stocks)

    for stock in rebalanced_stocks:
        stock["new_weight"] = round(
            (stock["new_weight"] / total_weight) * 100,
            2,
        )

    result = {
        "snapshot_type": "rebalance",
        "rebalanced_at": datetime.now(timezone.utc).isoformat(),
        "stocks": rebalanced_stocks,
    }

    save_rebalance_history(result)
    return result


def save_rebalance_history(result: dict) -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    history = load_rebalance_history()

    if not history or history[0].get("snapshot_type") != "initial":
        if history:
            first_timestamp = datetime.fromisoformat(
                history[0]["rebalanced_at"].replace("Z", "+00:00")
            )
            initial_timestamp = first_timestamp - timedelta(seconds=1)
        else:
            rebalance_timestamp = datetime.fromisoformat(
                result["rebalanced_at"].replace("Z", "+00:00")
            )
            initial_timestamp = rebalance_timestamp - timedelta(seconds=1)

        history.insert(0, create_initial_snapshot(initial_timestamp))

    history.append(result)
    HISTORY_FILE.write_text(json.dumps(history, indent=2))
