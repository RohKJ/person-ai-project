from __future__ import annotations

from datetime import timedelta

from app.analysis.ads import get_campaign_performance
from app.analysis.inventory import check_inventory_risk
from app.analysis.reviews import summarize_reviews
from app.analysis.sales import get_daily_sales_summary
from app.analysis.common import parse_date


def _format_money(value: float | int | None) -> str:
    if value is None:
        return "N/A"
    return f"{float(value):,.0f}원"


def generate_slack_report(
    report_type: str = "daily",
    date: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    target_date = parse_date(date)
    period_end = parse_date(end_date) if end_date else target_date
    period_start = parse_date(start_date) if start_date else period_end - timedelta(days=6)

    sales = get_daily_sales_summary(target_date.isoformat())
    ads = get_campaign_performance(period_start.isoformat(), period_end.isoformat())
    inventory = check_inventory_risk(days=7)
    reviews = summarize_reviews(period_start.isoformat(), period_end.isoformat())

    sales_metrics = sales["metrics"]
    ad_rows = ads["evidence"]
    total_spend = sum(float(row["spend"]) for row in ad_rows)
    total_attributed_sales = sum(float(row["attributed_sales"]) for row in ad_rows)
    blended_roas = round(total_attributed_sales / total_spend, 2) if total_spend else None
    risk_count = len(inventory["risk_items"])
    review_metrics = reviews["metrics"]
    top_keywords = ", ".join(
        f"{row['keyword']}({row['count']})" for row in reviews["complaint_keywords"][:3]
    ) or "없음"

    change = sales_metrics["sales_change_rate_pct"]
    change_text = "전일 데이터 없음" if change is None else f"{change:+.2f}%"
    text = "\n".join(
        [
            f"[{target_date.isoformat()} {report_type.upper()} 운영 리포트]",
            f"- 매출: {_format_money(sales_metrics['total_sales'])} / 주문 {sales_metrics['order_count']:,}건 / 판매수량 {sales_metrics['total_quantity']:,}개",
            f"- 전일 대비 매출 증감률: {change_text}",
            f"- 최근 {period_start.isoformat()}~{period_end.isoformat()} 광고비: {_format_money(total_spend)} / 광고 기여 매출: {_format_money(total_attributed_sales)} / ROAS: {blended_roas if blended_roas is not None else 'N/A'}",
            f"- 재고 리스크 상품: {risk_count}개",
            f"- 리뷰 평균 평점: {review_metrics['average_rating']} / 부정 리뷰: {review_metrics['negative_review_count']}건 / 주요 불만: {top_keywords}",
        ]
    )

    return {
        "tool_name": "generate_slack_report",
        "parameters": {
            "report_type": report_type,
            "date": target_date.isoformat(),
            "start_date": period_start.isoformat(),
            "end_date": period_end.isoformat(),
        },
        "report_text": text,
        "formula": {
            "report": "Composed only from get_daily_sales_summary, get_campaign_performance, check_inventory_risk, summarize_reviews outputs",
            "blended_roas": "SUM(ad attributed_sales) / SUM(ad spend)",
        },
        "evidence": {
            "sales": sales,
            "ads": ads,
            "inventory": inventory,
            "reviews": reviews,
        },
    }
