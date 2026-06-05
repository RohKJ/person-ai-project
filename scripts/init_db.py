from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import DB_PATH, SAMPLE_DATA_DIR
from app.core.database import engine
from app.models.tables import Base


DATE_COLUMNS = {
    "orders": ["order_date"],
    "ads": ["ad_date"],
    "inventory": ["inventory_date"],
    "reviews": ["review_date"],
    "cs_messages": ["message_date"],
}


def load_csv(table_name: str, filename: str) -> None:
    path = SAMPLE_DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"{path} does not exist. Run `python scripts/generate_sample_data.py` first."
        )

    dataframe = pd.read_csv(path, encoding="utf-8-sig")
    for column in DATE_COLUMNS.get(table_name, []):
        dataframe[column] = pd.to_datetime(dataframe[column]).dt.date

    dataframe.to_sql(table_name, engine, if_exists="append", index=False)
    print(f"loaded {table_name}: {len(dataframe):,} rows")


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    load_csv("products", "products.csv")
    load_csv("orders", "orders.csv")
    load_csv("ads", "ads.csv")
    load_csv("inventory", "inventory.csv")
    load_csv("reviews", "reviews.csv")
    load_csv("cs_messages", "cs_messages.csv")

    print(f"database ready: {DB_PATH}")


if __name__ == "__main__":
    main()
