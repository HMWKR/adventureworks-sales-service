# routers/predictions.py — 예측 로그 조회 API (Supabase/로컬)
from fastapi import APIRouter, Query

from app.services import log_service

router = APIRouter(prefix="/predictions", tags=["Predictions Log"])


@router.get("/recent")
def recent(limit: int = Query(10, ge=1, le=100)):
    """최근 예측 기록(최신순) + 저장소 종류."""
    return {"source": log_service.source(), "items": log_service.recent_predictions(limit)}
