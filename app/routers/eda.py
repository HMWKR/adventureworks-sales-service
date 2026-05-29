# routers/eda.py — EDA 집계 API
from fastapi import APIRouter

from app import schemas
from app.services import eda_service

router = APIRouter(prefix="/eda", tags=["EDA"])


@router.get("/summary")
def get_summary():
    """전체 요약 통계."""
    return eda_service.summary()


@router.get("/monthly-sales", response_model=list[schemas.MonthlySales])
def monthly_sales():
    """월별 매출 집계 (PPT 요구 엔드포인트)."""
    return eda_service.monthly_sales()


@router.get("/region-sales", response_model=list[schemas.RegionSales])
def region_sales():
    """지역별 매출 집계 (PPT 요구 엔드포인트)."""
    return eda_service.region_sales()


@router.get("/category-sales", response_model=list[schemas.CategorySales])
def category_sales():
    """카테고리별 매출 집계."""
    return eda_service.category_sales()


@router.get("/channel-sales")
def channel_sales():
    """채널별(Internet/Reseller) 매출 집계."""
    return eda_service.channel_sales()


@router.get("/top-products")
def top_products(n: int = 10):
    """매출 상위 제품."""
    return eda_service.top_products(n)
