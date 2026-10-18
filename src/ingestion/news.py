import time

import requests

from src.models import TextItem


GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
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

    company_query = (
        "Nvidia OR Tesla OR Apple OR JPMorgan OR Exxon "
        "OR Microsoft OR Amazon OR Alphabet OR Meta OR Walmart"
    )

    parameters = {
        "query": f"({company_query})",
        "mode": "artlist",
        "format": "json",
        "maxrecords": max_records,
        "timespan": "24h",
        "sort": "datedesc",
    }

    try:
        response = requests.get(
            GDELT_URL,
            params=parameters,
            timeout=15,
        )
        response.raise_for_status()

        articles = response.json().get("articles", [])
    except (requests.RequestException, ValueError):
        # Keep the most recently fetched live data available if GDELT is busy.
        return list(_cached_news)

    news_items = []

    for article in articles:
        title = article.get("title", "").strip()

        if not title:
            continue

        news_items.append(
            TextItem(
                source="gdelt_news",
                company=identify_company(title),
                text=title,
            )
        )

    if news_items:
        _cached_news = news_items
        _cache_expires_at = time.monotonic() + CACHE_TTL_SECONDS

    return list(news_items)
