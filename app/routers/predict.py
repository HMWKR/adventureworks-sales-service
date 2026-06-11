# routers/predict.py — ML 예측 API (회귀·분류·시계열)
from fastapi import APIRouter, Query, HTTPException

from app import schemas
from app.services import ml_service, log_service

router = APIRouter(prefix="/predict", tags=["Predict"])


@router.post("/sales", response_model=schemas.SalesPredictResponse)
def predict_sales(req: schemas.SalesPredictRequest):
    """매출 회귀 예측 (PPT 요구 엔드포인트)."""
    try:
        out = ml_service.predict_sales(
            order_quantity=req.order_quantity, list_price=req.list_price,
            standard_cost=req.standard_cost, category=req.category,
            subcategory=req.subcategory, channel=req.channel, region=req.region,
        )
    except ml_service.InvalidInput as e:
        raise HTTPException(status_code=400, detail=str(e))
    log_service.log_prediction("sales", req.model_dump(), out)
    return out


@router.post("/buy", response_model=schemas.BuyPredictResponse)
def predict_buy(req: schemas.BuyPredictRequest):
    """구매 예측 Buy or Not Buy (PPT 요구: 고객정보 → 구매 여부, CRM)."""
    try:
        out = ml_service.predict_buy(
            region=req.region, channel=req.channel, category=req.category,
            prior_orders=req.prior_orders, prior_monetary=req.prior_monetary,
        )
    except ml_service.InvalidInput as e:
        raise HTTPException(status_code=400, detail=str(e))
    log_service.log_prediction("buy", req.model_dump(), out)
    return out


@router.post("/segment", response_model=schemas.SegmentPredictResponse)
def predict_segment(req: schemas.SegmentPredictRequest):
    """고객 RFM 세그먼트 분류 예측 (보너스)."""
    out = ml_service.classify_segment(req.recency, req.frequency, req.monetary)
    log_service.log_prediction("segment", req.model_dump(),
                               {"segment": out["segment"], "confidence": out["confidence"]})
    return out


@router.get("/forecast", response_model=schemas.ForecastResponse)
def forecast(horizon: int = Query(6, ge=1, le=24)):
    """월매출 시계열 예측(향후 N개월)."""
    return ml_service.forecast_monthly(horizon)
