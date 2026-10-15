from pathlib import Path
import pandas as pd

from src.models import TextItem


DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data" / "raw"


def load_text_items() -> list[TextItem]:
    items = []

    for file_name in ["news.csv", "social_posts.csv"]:
        file_path = DATA_DIRECTORY / file_name
        data = pd.read_csv(file_path)

        for _, row in data.iterrows():
            items.append(
                TextItem(
                    source=str(row["source"]),
                    company=str(row["company"]),
                    text=str(row["text"]),
                )
            )

    return items
