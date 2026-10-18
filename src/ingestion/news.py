import os
import time
import hashlib
import json
from pathlib import Path

import requests
from dotenv import load_dotenv

from src.models import TextItem


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

NEWS_API_URL = "https://newsapi.org/v2/everything"
CACHE_TTL_SECONDS = 60
SEEN_NEWS_FILE = PROJECT_ROOT / "data" / "processed" / "seen_news_articles.json"

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


def load_seen_news_ids() -> set[str]:
    if not SEEN_NEWS_FILE.exists():
        return set()

    try:
        return set(json.loads(SEEN_NEWS_FILE.read_text()))
    except (json.JSONDecodeError, OSError):
        return set()


def filter_unseen_news(news_items: list[TextItem]) -> list[TextItem]:
    seen_ids = load_seen_news_ids()
    ids_in_current_batch = set()
    unseen_items = []

    for item in news_items:
        if not item.item_id:
            continue
        if item.item_id in seen_ids or item.item_id in ids_in_current_batch:
            continue

        ids_in_current_batch.add(item.item_id)
        unseen_items.append(item)

    return unseen_items


def mark_news_as_processed(items: list[TextItem]) -> None:
    processed_ids = {
        item.item_id
        for item in items
        if item.source == "newsapi" and item.item_id
    }

    if not processed_ids:
        return

    SEEN_NEWS_FILE.parent.mkdir(parents=True, exist_ok=True)
    all_seen_ids = load_seen_news_ids() | processed_ids
    SEEN_NEWS_FILE.write_text(json.dumps(sorted(all_seen_ids), indent=2))


def reset_seen_news() -> None:
    SEEN_NEWS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SEEN_NEWS_FILE.write_text("[]")


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
        article_id = article.get("url")

        if not article_id:
            identifier_source = f"{title}|{article.get('publishedAt', '')}"
            article_id = hashlib.sha256(identifier_source.encode()).hexdigest()

        news_items.append(
            TextItem(
                source="newsapi",
                company=identify_company(text),
                text=text,
                item_id=article_id,
            )
        )

    if news_items:
        _cached_news = news_items
        _cache_expires_at = time.monotonic() + CACHE_TTL_SECONDS

    return list(news_items)
