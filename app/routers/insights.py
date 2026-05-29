# routers/insights.py — 자동 인사이트 API
from fastapi import APIRouter

from app.services import insight_service

router = APIRouter(prefix="/insights", tags=["Insights"])


@router.get("")
def insights():
    """대시보드용 자동 내러티브 인사이트."""
    return insight_service.generate_insights()


@router.get("/dashboard")
def dashboard_data():
    """스토리 대시보드 전체 데이터 번들(차트+인사이트)."""
    return insight_service.build_dashboard_payload()
