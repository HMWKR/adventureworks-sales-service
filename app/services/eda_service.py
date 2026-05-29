# eda_service.py — EDA 집계 (CRISP-DM: 데이터 이해)
# ------------------------------------------------------------
# 전처리 데이터로 월별/지역별/카테고리별/채널별 매출 집계를 제공한다.
# PPT 요구: GET /eda/monthly-sales, GET /eda/region-sales
# ------------------------------------------------------------
import pandas as pd

from app import data_access


def _df() -> pd.DataFrame:
    return data_access.get_dataframe()


def monthly_sales() -> list[dict]:
    """월별 매출/주문수/수량 집계 (시계열 순 정렬)."""
    df = _df()
    g = df.groupby("YearMonth").agg(
        sales_amount=("Sales Amount", "sum"),
        order_quantity=("Order Quantity", "sum"),
        order_lines=("Sales Amount", "size"),
    ).reset_index().sort_values("YearMonth")
    g["sales_amount"] = g["sales_amount"].round(2)
    return g.to_dict(orient="records")


def region_sales() -> list[dict]:
    """지역별 매출 집계 (매출 내림차순)."""
    df = _df()
    g = df.groupby("Region").agg(
        sales_amount=("Sales Amount", "sum"),
        order_quantity=("Order Quantity", "sum"),
        order_lines=("Sales Amount", "size"),
    ).reset_index().sort_values("sales_amount", ascending=False)
    g["sales_amount"] = g["sales_amount"].round(2)
    return g.to_dict(orient="records")


def category_sales() -> list[dict]:
    """카테고리별 매출 집계."""
    df = _df()
    g = df.groupby("Category").agg(
        sales_amount=("Sales Amount", "sum"),
        order_quantity=("Order Quantity", "sum"),
        order_lines=("Sales Amount", "size"),
    ).reset_index().sort_values("sales_amount", ascending=False)
    g["sales_amount"] = g["sales_amount"].round(2)
    return g.to_dict(orient="records")


def channel_sales() -> list[dict]:
    """채널별(Internet/Reseller) 매출 집계."""
    df = _df()
    g = df.groupby("Channel").agg(
        sales_amount=("Sales Amount", "sum"),
        order_quantity=("Order Quantity", "sum"),
        order_lines=("Sales Amount", "size"),
    ).reset_index().sort_values("sales_amount", ascending=False)
    g["sales_amount"] = g["sales_amount"].round(2)
    return g.to_dict(orient="records")


def top_products(n: int = 10) -> list[dict]:
    """매출 상위 제품."""
    df = _df()
    g = df.groupby("Product").agg(
        sales_amount=("Sales Amount", "sum"),
        order_quantity=("Order Quantity", "sum"),
    ).reset_index().sort_values("sales_amount", ascending=False).head(n)
    g["sales_amount"] = g["sales_amount"].round(2)
    return g.to_dict(orient="records")


def summary() -> dict:
    """전체 요약 통계 (대시보드 헤더용)."""
    df = _df()
    return {
        "total_sales": round(float(df["Sales Amount"].sum()), 2),
        "total_orders": int(df["Sales Order"].nunique()),
        "total_order_lines": int(len(df)),
        "total_quantity": int(df["Order Quantity"].sum()),
        "unique_buyers": int(df["Buyer"].nunique()),
        "unique_products": int(df["Product"].nunique()),
        "n_regions": int(df["Region"].nunique()),
        "n_months": int(df["YearMonth"].nunique()),
        "date_from": str(df["Date"].min().date()),
        "date_to": str(df["Date"].max().date()),
        "avg_order_value": round(float(df["Sales Amount"].mean()), 2),
    }
