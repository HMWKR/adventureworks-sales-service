# routers/rfm.py — RFM 분석 API
from fastapi import APIRouter, HTTPException

from app import schemas
from app.services import rfm_service

router = APIRouter(prefix="/rfm", tags=["RFM"])


@router.get("/segments", response_model=list[schemas.SegmentSummary])
def segments():
    """세그먼트별 요약(고객 수·평균 RFM·총 매출)."""
    return rfm_service.segment_summary()


@router.get("/top-customers", response_model=list[schemas.CustomerRFM])
def top_customers(n: int = 20):
    """Monetary 상위 고객."""
    rows = rfm_service.top_customers(n)
    # 키 이름을 응답 스키마에 맞게 정규화
    return [{
        "buyer": r["Buyer"], "recency": int(r["Recency"]),
        "frequency": int(r["Frequency"]), "monetary": float(r["Monetary"]),
        "rfm_score": r["RFM_Score"], "segment": r["Segment"],
    } for r in rows]


@router.get("/customer/{buyer}", response_model=schemas.CustomerRFM)
def customer(buyer: str):
    """특정 구매자 RFM 조회."""
    result = rfm_service.lookup(buyer)
    if result is None:
        raise HTTPException(status_code=404, detail="해당 구매자를 찾을 수 없습니다.")
    return result
