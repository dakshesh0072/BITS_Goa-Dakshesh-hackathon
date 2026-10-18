from pathlib import Path

import pandas as pd

from src.ingestion.news import fetch_live_news, filter_unseen_news
from src.models import TextItem


DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data" / "raw"


def load_csv_items(file_name: str) -> list[TextItem]:
    file_path = DATA_DIRECTORY / file_name
    data = pd.read_csv(file_path)

    return [
        TextItem(
            source=str(row["source"]),
            company=str(row["company"]),
            text=str(row["text"]),
        )
        for _, row in data.iterrows()
    ]


def load_text_items() -> list[TextItem]:
    live_news = filter_unseen_news(fetch_live_news())
    social_posts = load_csv_items("social_posts.csv")

    return live_news + social_posts
