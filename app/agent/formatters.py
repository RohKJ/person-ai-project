from __future__ import annotations

from typing import Any


def format_money(value: float | int | None) -> str:
    if value is None:
        return "N/A"
    return f"{float(value):,.0f}원"


def format_pct(value: float | int | None) -> str:
    if value is None:
        return "N/A"
    return f"{float(value):+.2f}%"


def format_daily_sales_answer(result: dict[str, Any]) -> str:
    metrics = result["metrics"]
    return (
        f"{result['parameters']['date']} 매출은 {format_money(metrics['total_sales'])}, "
        f"주문 {metrics['order_count']:,}건, 판매수량 {metrics['total_quantity']:,}개입니다. "
        f"전일 대비 매출 증감률은 {format_pct(metrics['sales_change_rate_pct'])}입니다."
    )


def format_campaign_performance_answer(result: dict[str, Any]) -> str:
    rows = result["evidence"]
    spend = sum(float(row["spend"]) for row in rows)
    sales = sum(float(row["attributed_sales"]) for row in rows)
    roas = round(sales / spend, 2) if spend else None
    top = max(rows, key=lambda row: float(row["attributed_sales"])) if rows else None
    top_text = f" 최고 기여 매출 캠페인은 {top['campaign_name']}입니다." if top else ""
    return (
        f"{result['parameters']['start_date']}~{result['parameters']['end_date']} 광고비는 {format_money(spend)}, "
        f"광고 기여 매출은 {format_money(sales)}, 통합 ROAS는 {roas if roas is not None else 'N/A'}입니다."
        f"{top_text}"
    )


def format_inventory_risk_answer(result: dict[str, Any]) -> str:
    risk_count = len(result["risk_items"])
    names = ", ".join(row["product_name"] for row in result["risk_items"][:3]) or "없음"
    return f"재고 리스크 상품은 {risk_count}개입니다. 우선 확인 대상은 {names}입니다."


def format_review_summary_answer(result: dict[str, Any]) -> str:
    metrics = result["metrics"]
    keywords = ", ".join(
        f"{row['keyword']}({row['count']})" for row in result["complaint_keywords"][:3]
    ) or "없음"
    return (
        f"평균 평점은 {metrics['average_rating']}, 부정 리뷰는 {metrics['negative_review_count']}건입니다. "
        f"주요 불만 키워드는 {keywords}입니다."
    )


def format_sales_anomaly_answer(result: dict[str, Any]) -> str:
    anomalies = result["anomalies"]
    if not anomalies:
        return (
            f"{result['parameters']['start_date']}~{result['parameters']['end_date']} 기간에 "
            "기준치를 넘는 매출 급등/급락 상품은 없습니다."
        )

    highlights = []
    for row in anomalies[:3]:
        direction = "급등" if row["direction"] == "surge" else "급락"
        highlights.append(f"{row['product_name']} {direction}({row['change_rate_pct']:+.2f}%)")

    return (
        f"{result['parameters']['start_date']}~{result['parameters']['end_date']} 기간에 "
        f"매출 이상 상품 {len(anomalies)}개가 탐지됐습니다. "
        f"주요 항목은 {', '.join(highlights)}입니다."
    )


def format_slack_report_answer(result: dict[str, Any]) -> str:
    return result["report_text"]
