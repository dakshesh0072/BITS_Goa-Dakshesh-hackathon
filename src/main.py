from fastapi import FastAPI
from src.models import RiskSignal, TextItem
from src.pipeline import analyze_text

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