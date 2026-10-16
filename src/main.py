from fastapi import FastAPI

from src.ingestion.loader import load_text_items
from src.models import RiskSignal, TextItem
from src.pipeline import analyze_text
from src.rebalancer import (
    load_rebalance_history,
    rebalance_index,
    reset_rebalance_history,
)

app = FastAPI(
    title="AI/NLP Financial Risk Engine",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/analyze", response_model=RiskSignal)
def analyze(item: TextItem):
    return analyze_text(item)


@app.post("/analyze/batch", response_model=list[RiskSignal])
def analyze_batch():
    items = load_text_items()
    return [analyze_text(item) for item in items]


@app.post("/rebalance")
def rebalance():
    items = load_text_items()
    signals = [analyze_text(item) for item in items]
    return rebalance_index(signals)


@app.get("/history")
def history():
    return load_rebalance_history()


@app.post("/reset")
def reset_portfolio():
    return reset_rebalance_history()
