from datetime import datetime, timedelta, timezone
from pathlib import Path
import json

import pandas as pd

from src.models import RiskSignal


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STOCKS_FILE = PROJECT_ROOT / "data" / "raw" / "stocks.csv"
HISTORY_FILE = PROJECT_ROOT / "data" / "processed" / "rebalance_history.json"


def rebalance_index(signals: list[RiskSignal]) -> dict:
    stocks = pd.read_csv(STOCKS_FILE)
    rebalanced_stocks = []

    for _, stock in stocks.iterrows():
        ticker = stock["ticker"]
        base_weight = float(stock["base_weight"])

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

        adjusted_weight = base_weight * (1 + 0.10 * average_sentiment)
        adjusted_weight = max(0.03, min(0.18, adjusted_weight))

        rebalanced_stocks.append(
            {
                "ticker": ticker,
                "base_weight": round(base_weight * 100, 2),
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
        "rebalanced_at": datetime.now(timezone.utc).isoformat(),
        "stocks": rebalanced_stocks,
    }

    save_rebalance_history(result)
    return result


def save_rebalance_history(result: dict) -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    if HISTORY_FILE.exists():
        history = json.loads(HISTORY_FILE.read_text())
    else:
        history = []

    needs_initial_snapshot = (
        not history or history[0].get("snapshot_type") != "initial"
    )

    if needs_initial_snapshot:
        if history:
            first_timestamp = datetime.fromisoformat(
                history[0]["rebalanced_at"].replace("Z", "+00:00")
            )
        else:
            first_timestamp = datetime.fromisoformat(
                result["rebalanced_at"].replace("Z", "+00:00")
            )

        initial_stocks = []

        for stock in result["stocks"]:
            initial_stocks.append(
                {
                    "ticker": stock["ticker"],
                    "base_weight": stock["base_weight"],
                    "sentiment_score": 0.0,
                    "new_weight": stock["base_weight"],
                }
            )

        history.insert(
            0,
            {
                "snapshot_type": "initial",
                "rebalanced_at": (
                    first_timestamp - timedelta(seconds=1)
                ).isoformat(),
                "stocks": initial_stocks,
            },
        )

    history.append(result)
    HISTORY_FILE.write_text(json.dumps(history, indent=2))


def load_rebalance_history() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []

    return json.loads(HISTORY_FILE.read_text())
