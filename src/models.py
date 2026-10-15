from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class EventType(str, Enum):
    GEOPOLITICAL = "Geopolitical"
    MACROECONOMIC = "Macroeconomic"
    CREDIT_EVENT = "Credit Event"
    MERGER_ACQUISITION = "Merger/Acquisition"
    EARNINGS = "Earnings"
    PRODUCT_LAUNCH = "Product Launch"
    REGULATORY = "Regulatory"
    MARKET_MOVEMENT = "Market Movement"
    OTHER = "Other"


class TextItem(BaseModel):
    source: str = Field(examples=["news", "social"])
    text: str
    company: str | None = None


class RiskSignal(BaseModel):
    source: str
    text: str
    company: str | None
    sentiment_score: float
    event_classification: EventType
    impact_score: int
    processed_at: datetime