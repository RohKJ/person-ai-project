from __future__ import annotations

from collections import Counter

from app.analysis.common import dataframe_records, date_to_str, read_sql, round_or_none


COMPLAINT_KEYWORDS = {
    "향": ["향", "냄새"],
    "배송": ["배송", "샜", "상자"],
    "가격": ["가격", "용량"],
    "두피 자극": ["두피", "간지럽", "자극"],
    "펌프/패키징": ["펌프", "패키지", "용기"],
    "효과": ["효과", "모르겠"],
    "끈적임": ["끈적"],
}


def summarize_reviews(start_date: str, end_date: str) -> dict:
    start = date_to_str(start_date)
    end = date_to_str(end_date)
    reviews_query = """
        SELECT
            r.review_id,
            r.review_date,
            r.product_id,
            p.product_name,
            r.rating,
            r.review_text
        FROM reviews r
        JOIN products p ON p.product_id = r.product_id
        WHERE r.review_date BETWEEN :start_date AND :end_date
        ORDER BY r.review_date DESC
    """
    cs_query = """
        SELECT
            category,
            status,
            COUNT(*) AS message_count
        FROM cs_messages
        WHERE message_date BETWEEN :start_date AND :end_date
        GROUP BY category, status
        ORDER BY message_count DESC
    """
    reviews = read_sql(reviews_query, {"start_date": start, "end_date": end})
    cs_messages = read_sql(cs_query, {"start_date": start, "end_date": end})

    average_rating = round_or_none(float(reviews["rating"].mean()), 2) if not reviews.empty else None
    negative_reviews = reviews[reviews["rating"] <= 2].copy() if not reviews.empty else reviews

    keyword_counter: Counter[str] = Counter()
    for text in negative_reviews["review_text"].fillna(""):
        for label, keywords in COMPLAINT_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                keyword_counter[label] += 1

    keyword_rows = [
        {"keyword": keyword, "count": count}
        for keyword, count in keyword_counter.most_common()
    ]

    return {
        "tool_name": "summarize_reviews",
        "parameters": {"start_date": start, "end_date": end},
        "metrics": {
            "average_rating": average_rating,
            "review_count": int(len(reviews)),
            "negative_review_count": int(len(negative_reviews)),
        },
        "formula": {
            "average_rating": "AVG(reviews.rating)",
            "negative_review_count": "COUNT(reviews.rating <= 2)",
            "complaint_keywords": "Rule-based keyword count over negative review_text",
        },
        "complaint_keywords": keyword_rows,
        "negative_reviews": dataframe_records(negative_reviews.head(20)),
        "cs_summary": dataframe_records(cs_messages),
        "evidence": dataframe_records(reviews.head(50)),
    }
