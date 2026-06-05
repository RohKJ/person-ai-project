from __future__ import annotations

import random
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import DEFAULT_BRAND, SAMPLE_DATA_DIR


RNG = random.Random(42)


def build_products() -> pd.DataFrame:
    products = [
        ("LR-SHP-001", "Scalp Cloud Balancing Shampoo", "Shampoo", 29000),
        ("LR-CND-002", "Silk Flow Lightweight Conditioner", "Conditioner", 27000),
        ("LR-TRT-003", "Root Revival Ampoule Treatment", "Treatment", 39000),
        ("LR-OIL-004", "Velvet Ends Hair Oil", "Hair Oil", 32000),
        ("LR-MSK-005", "Deep Dew Repair Hair Mask", "Hair Mask", 36000),
        ("LR-TON-006", "Calm Mint Scalp Tonic", "Scalp Care", 31000),
        ("LR-SER-007", "Frizz Shield Leave-in Serum", "Serum", 34000),
        ("LR-KIT-008", "7-Day Gloss Reset Kit", "Routine Kit", 69000),
    ]
    return pd.DataFrame(
        products,
        columns=["product_id", "product_name", "category", "price"],
    ).assign(brand=DEFAULT_BRAND)[
        ["product_id", "product_name", "brand", "category", "price"]
    ]


def daterange(start_date: date, end_date: date) -> list[date]:
    days = (end_date - start_date).days
    return [start_date + timedelta(days=offset) for offset in range(days + 1)]


def build_orders(products: pd.DataFrame, start_date: date, end_date: date) -> pd.DataFrame:
    channels = ["D2C Store", "Naver SmartStore", "Kakao Gift", "Amazon US"]
    base_demand = {
        "LR-SHP-001": 22,
        "LR-CND-002": 18,
        "LR-TRT-003": 13,
        "LR-OIL-004": 15,
        "LR-MSK-005": 11,
        "LR-TON-006": 10,
        "LR-SER-007": 12,
        "LR-KIT-008": 6,
    }
    price_by_product = dict(zip(products["product_id"], products["price"], strict=True))
    rows: list[dict[str, object]] = []
    order_seq = 1

    for current_date in daterange(start_date, end_date):
        is_weekend = current_date.weekday() >= 5
        for product_id, base in base_demand.items():
            multiplier = 1.18 if is_weekend else 1.0

            if product_id == "LR-MSK-005" and current_date >= end_date - timedelta(days=6):
                multiplier *= 1.85
            if product_id == "LR-TON-006" and current_date >= end_date - timedelta(days=6):
                multiplier *= 0.35

            estimated_orders = max(1, int(RNG.gauss(base * multiplier, base * 0.25)))
            for _ in range(estimated_orders):
                quantity = RNG.choices([1, 2, 3], weights=[0.72, 0.22, 0.06])[0]
                price = float(price_by_product[product_id])
                gross_sales = price * quantity
                discount_rate = RNG.choices(
                    [0.0, 0.05, 0.1, 0.15, 0.2],
                    weights=[0.48, 0.2, 0.17, 0.1, 0.05],
                )[0]
                discount_amount = round(gross_sales * discount_rate, 2)
                rows.append(
                    {
                        "order_id": f"O-{order_seq:06d}",
                        "order_date": current_date.isoformat(),
                        "product_id": product_id,
                        "channel": RNG.choices(
                            channels,
                            weights=[0.58, 0.24, 0.11, 0.07],
                        )[0],
                        "quantity": quantity,
                        "sales_amount": round(gross_sales - discount_amount, 2),
                        "discount_amount": discount_amount,
                    }
                )
                order_seq += 1

    return pd.DataFrame(rows)


def build_ads(products: pd.DataFrame, start_date: date, end_date: date) -> pd.DataFrame:
    price_by_product = dict(zip(products["product_id"], products["price"], strict=True))
    campaigns = [
        ("CAMP-001", "Scalp Balance Search", "LR-SHP-001", 0.036, 0.052),
        ("CAMP-002", "Repair Mask Retargeting", "LR-MSK-005", 0.028, 0.071),
        ("CAMP-003", "Gloss Kit Launch", "LR-KIT-008", 0.022, 0.047),
        ("CAMP-004", "Frizz Serum Social", "LR-SER-007", 0.031, 0.038),
    ]
    rows: list[dict[str, object]] = []

    for current_date in daterange(start_date, end_date):
        for campaign_id, campaign_name, product_id, base_ctr, base_cvr in campaigns:
            spend = round(RNG.uniform(70000, 260000), 2)
            impressions = max(1000, int(spend / RNG.uniform(35, 70)))
            ctr = max(0.003, RNG.gauss(base_ctr, 0.006))
            clicks = max(1, int(impressions * ctr))
            cvr = max(0.002, RNG.gauss(base_cvr, 0.012))
            conversions = max(0, int(clicks * cvr))

            if product_id == "LR-MSK-005" and current_date >= end_date - timedelta(days=6):
                conversions = int(conversions * 1.5) + 2

            attributed_sales = round(conversions * float(price_by_product[product_id]) * RNG.uniform(0.9, 1.35), 2)
            rows.append(
                {
                    "ad_date": current_date.isoformat(),
                    "campaign_id": campaign_id,
                    "campaign_name": campaign_name,
                    "product_id": product_id,
                    "spend": spend,
                    "impressions": impressions,
                    "clicks": clicks,
                    "conversions": conversions,
                    "attributed_sales": attributed_sales,
                }
            )

    return pd.DataFrame(rows)


def build_inventory(products: pd.DataFrame, orders: pd.DataFrame, start_date: date, end_date: date) -> pd.DataFrame:
    starting_stock = {
        "LR-SHP-001": 980,
        "LR-CND-002": 820,
        "LR-TRT-003": 620,
        "LR-OIL-004": 700,
        "LR-MSK-005": 360,
        "LR-TON-006": 460,
        "LR-SER-007": 540,
        "LR-KIT-008": 210,
    }
    safety_stock = {
        "LR-SHP-001": 180,
        "LR-CND-002": 150,
        "LR-TRT-003": 100,
        "LR-OIL-004": 120,
        "LR-MSK-005": 120,
        "LR-TON-006": 90,
        "LR-SER-007": 90,
        "LR-KIT-008": 45,
    }
    sales_by_day = (
        orders.groupby(["order_date", "product_id"], as_index=False)["quantity"].sum()
        if not orders.empty
        else pd.DataFrame(columns=["order_date", "product_id", "quantity"])
    )
    sales_lookup = {
        (row.order_date, row.product_id): int(row.quantity)
        for row in sales_by_day.itertuples(index=False)
    }
    stock_by_product = starting_stock.copy()
    rows: list[dict[str, object]] = []

    for current_date in daterange(start_date, end_date):
        for product_id in products["product_id"]:
            sold = sales_lookup.get((current_date.isoformat(), product_id), 0)
            stock_by_product[product_id] = max(0, stock_by_product[product_id] - sold)

            if current_date.day in {1, 15} and product_id not in {"LR-MSK-005", "LR-KIT-008"}:
                stock_by_product[product_id] += RNG.randint(120, 260)

            rows.append(
                {
                    "inventory_date": current_date.isoformat(),
                    "product_id": product_id,
                    "stock_quantity": stock_by_product[product_id],
                    "safety_stock": safety_stock[product_id],
                }
            )

    return pd.DataFrame(rows)


def build_reviews(products: pd.DataFrame, start_date: date, end_date: date) -> pd.DataFrame:
    positive_texts = [
        "두피가 편안하고 향도 은은해서 재구매 의향이 있어요.",
        "머릿결이 부드러워지고 사용감이 가벼워요.",
        "배송이 빠르고 패키지도 깔끔해서 선물용으로 좋아요.",
        "한 주 정도 쓰니 푸석함이 줄어든 느낌이에요.",
    ]
    negative_texts = [
        "향이 생각보다 강해서 아쉬웠어요.",
        "펌프가 잘 눌리지 않아 사용이 불편했어요.",
        "가격 대비 용량이 작게 느껴져요.",
        "두피가 살짝 간지럽고 효과를 아직 모르겠어요.",
        "배송 중 내용물이 조금 샜어요.",
        "오일이 제 모발에는 끈적임이 남았어요.",
    ]
    rows: list[dict[str, object]] = []
    dates = daterange(start_date, end_date)

    for idx in range(1, 241):
        product_id = RNG.choice(list(products["product_id"]))
        rating = RNG.choices([1, 2, 3, 4, 5], weights=[0.07, 0.11, 0.16, 0.33, 0.33])[0]
        review_text = RNG.choice(negative_texts if rating <= 2 else positive_texts)
        rows.append(
            {
                "review_id": f"R-{idx:05d}",
                "review_date": RNG.choice(dates).isoformat(),
                "product_id": product_id,
                "rating": rating,
                "review_text": review_text,
            }
        )

    return pd.DataFrame(rows).sort_values(["review_date", "review_id"])


def build_cs_messages(products: pd.DataFrame, start_date: date, end_date: date) -> pd.DataFrame:
    categories = {
        "배송": [
            "배송 일정 확인 부탁드립니다.",
            "상자가 찌그러져 도착했어요.",
            "배송지가 잘못 입력되어 변경하고 싶어요.",
        ],
        "상품": [
            "두피가 민감한 편인데 사용 가능할까요?",
            "펌프 불량으로 교환 요청드립니다.",
            "향 지속 시간이 궁금합니다.",
        ],
        "반품/교환": [
            "개봉 후 교환이 가능한지 문의드립니다.",
            "다른 상품으로 교환하고 싶어요.",
            "환불 처리 상태 확인 부탁드립니다.",
        ],
        "구독": [
            "정기배송 주기를 변경하고 싶어요.",
            "이번 달 구독을 건너뛰고 싶습니다.",
            "구독 할인 적용 여부가 궁금합니다.",
        ],
        "결제": [
            "쿠폰이 결제 단계에서 적용되지 않습니다.",
            "영수증 발급 부탁드립니다.",
            "중복 결제된 것 같아요.",
        ],
    }
    rows: list[dict[str, object]] = []
    dates = daterange(start_date, end_date)

    for idx in range(1, 181):
        category = RNG.choice(list(categories))
        rows.append(
            {
                "message_id": f"CS-{idx:05d}",
                "message_date": RNG.choice(dates).isoformat(),
                "product_id": RNG.choice(list(products["product_id"])),
                "category": category,
                "message": RNG.choice(categories[category]),
                "status": RNG.choices(["open", "pending", "resolved"], weights=[0.18, 0.22, 0.6])[0],
            }
        )

    return pd.DataFrame(rows).sort_values(["message_date", "message_id"])


def main() -> None:
    SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    end_date = date.today()
    start_date = end_date - timedelta(days=44)

    products = build_products()
    orders = build_orders(products, start_date, end_date)
    ads = build_ads(products, start_date, end_date)
    inventory = build_inventory(products, orders, start_date, end_date)
    reviews = build_reviews(products, start_date, end_date)
    cs_messages = build_cs_messages(products, start_date, end_date)

    datasets = {
        "products.csv": products,
        "orders.csv": orders,
        "ads.csv": ads,
        "inventory.csv": inventory,
        "reviews.csv": reviews,
        "cs_messages.csv": cs_messages,
    }
    for filename, dataframe in datasets.items():
        dataframe.to_csv(SAMPLE_DATA_DIR / filename, index=False, encoding="utf-8-sig")
        print(f"created {SAMPLE_DATA_DIR / filename} ({len(dataframe):,} rows)")


if __name__ == "__main__":
    main()
