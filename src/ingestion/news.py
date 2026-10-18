import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

from src.models import TextItem


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

NEWS_API_URL = "https://newsapi.org/v2/everything"
CACHE_TTL_SECONDS = 60

_cached_news: list[TextItem] = []
_cache_expires_at = 0.0

COMPANIES = {
    "NVDA": ["nvidia", "nvda"],
    "TSLA": ["tesla", "tsla"],
    "AAPL": ["apple", "aapl"],
    "JPM": ["jpmorgan", "j.p. morgan", "jpm"],
    "XOM": ["exxon", "exxon mobil", "xom"],
    "MSFT": ["microsoft", "msft"],
    "AMZN": ["amazon", "amzn"],
    "GOOGL": ["alphabet", "google", "googl"],
    "META": ["meta", "facebook"],
    "WMT": ["walmart", "wmt"],
}


def identify_company(text: str) -> str | None:
    normalized_text = text.lower()

    for ticker, names in COMPANIES.items():
        if any(name in normalized_text for name in names):
            return ticker

    return None


def fetch_live_news(max_records: int = 5) -> list[TextItem]:
    global _cached_news, _cache_expires_at

    if _cached_news and time.monotonic() < _cache_expires_at:
        return list(_cached_news)

    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return list(_cached_news)

    company_query = " OR ".join(
        [
            "Nvidia",
            "Tesla",
            "Apple",
            "JPMorgan",
            "Exxon",
            "Microsoft",
            "Amazon",
            "Alphabet",
            "Meta",
            "Walmart",
        ]
    )

    parameters = {
        "q": f"({company_query})",
        "searchIn": "title,description",
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": max_records,
        "apiKey": api_key,
    }

    try:
        response = requests.get(
            NEWS_API_URL,
            params=parameters,
            timeout=15,
        )
        response.raise_for_status()

        articles = response.json().get("articles", [])
    except requests.RequestException:
        # Keep the most recently fetched live data available if NewsAPI is busy.
        return list(_cached_news)
    except ValueError:
        return list(_cached_news)

    news_items = []

    for article in articles:
        title = article.get("title", "").strip()
        description = (article.get("description") or "").strip()

        if not title:
            continue

        text = f"{title}. {description}" if description else title

        news_items.append(
            TextItem(
                source="newsapi",
                company=identify_company(text),
                text=text,
            )
        )

    if news_items:
        _cached_news = news_items
        _cache_expires_at = time.monotonic() + CACHE_TTL_SECONDS

    return list(news_items)
