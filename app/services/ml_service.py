# ml_service.py — 학습된 모델 로딩 + 추론 (CRISP-DM: 배포)
# ------------------------------------------------------------
# models/*.pkl 을 지연 로딩(캐시)하고 예측 함수를 제공한다.
# 모델이 없으면 학습을 자동 트리거한다.
# ------------------------------------------------------------
import pickle
from functools import lru_cache

import numpy as np
import pandas as pd

from app import config


class ModelNotReady(Exception):
    """모델 파일이 없고 학습도 불가할 때."""


class InvalidInput(ValueError):
    """예측 입력값이 허용 범위를 벗어났을 때(라우터에서 400으로 변환)."""


def _ensure_models() -> None:
    """모델 3종이 모두 없으면 학습을 1회 실행한다."""
    if not (config.REG_MODEL.exists() and config.CLF_MODEL.exists()
            and config.TS_MODEL.exists()):
        from app.ml import train
        train.train_all()


def _safe_pickle_load(path):
    """모델 파일 로드(손상/누락 시 명확한 오류)."""
    if not path.exists():
        raise ModelNotReady(f"모델 파일 없음: {path}")
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except (pickle.UnpicklingError, EOFError, OSError) as e:
        raise RuntimeError(f"모델 로드 실패({path.name}): {e}") from e


@lru_cache(maxsize=1)
def _load() -> dict:
    _ensure_models()
    return {
        "reg": _safe_pickle_load(config.REG_MODEL),
        "clf": _safe_pickle_load(config.CLF_MODEL),
        "ts": _safe_pickle_load(config.TS_MODEL),
    }


def reset_cache() -> None:
    _load.cache_clear()


# ── 1. 매출 회귀 예측 ────────────────────────────────────────
def predict_sales(order_quantity: int, list_price: float, standard_cost: float,
                  category: str, subcategory: str, channel: str, region: str) -> dict:
    bundle = _load()["reg"]
    model = bundle["model"]
    feats = bundle["features"]
    cat_values = bundle.get("cat_values", {})

    row_dict = {
        "Order Quantity": order_quantity,
        "List Price": list_price,
        "Standard Cost": standard_cost,
        "Category": category,
        "Subcategory": subcategory,
        "Channel": channel,
        "Region": region,
    }
    # 범주형 입력 검증: 학습에 없던 값은 OneHotEncoder가 전부 0으로 무시 →
    # 신뢰할 수 없는 예측이 되므로 사전 차단한다.
    for col in ("Category", "Subcategory", "Channel", "Region"):
        allowed = cat_values.get(col)
        if allowed and str(row_dict[col]) not in allowed:
            preview = ", ".join(allowed[:8]) + ("..." if len(allowed) > 8 else "")
            raise InvalidInput(f"알 수 없는 {col} 값: '{row_dict[col]}' (허용: {preview})")

    # 저장된 피처 순서대로 정렬하여 전달(ColumnTransformer 정합성·가독성)
    row = pd.DataFrame([{k: row_dict[k] for k in feats}])
    pred = float(model.predict(row)[0])
    return {"predicted_sales_amount": round(pred, 2)}


# ── 2. 고객 RFM 세그먼트 분류 예측 ───────────────────────────
def classify_segment(recency: int, frequency: int, monetary: float) -> dict:
    bundle = _load()["clf"]
    model = bundle["model"]
    X = pd.DataFrame([{"Recency": recency, "Frequency": frequency, "Monetary": monetary}])
    pred = model.predict(X)[0]
    proba = model.predict_proba(X)[0]
    classes = list(model.classes_)
    prob_map = {c: round(float(p), 4) for c, p in zip(classes, proba)}
    return {
        "segment": str(pred),
        "confidence": round(float(np.max(proba)), 4),
        "probabilities": dict(sorted(prob_map.items(), key=lambda x: -x[1])),
    }


# ── 3. 월매출 시계열 예측 ────────────────────────────────────
def forecast_monthly(horizon: int | None = None) -> dict:
    bundle = _load()["ts"]
    fit = bundle["fit"]
    h = horizon or bundle["horizon"]
    h = max(1, min(int(h), 24))   # 1~24개월 제한

    fc = np.asarray(fit.forecast(h), dtype=float)
    last = pd.Period(bundle["index"][-1], freq="M")
    future = [(last + i + 1).strftime("%Y-%m") for i in range(h)]

    history = [
        {"month": m, "sales_amount": round(float(v), 2)}
        for m, v in zip(bundle["index"], bundle["values"])
    ]
    forecast = [
        {"month": m, "forecast_sales_amount": round(float(v), 2)}
        for m, v in zip(future, fc)
    ]
    return {"horizon": h, "history": history, "forecast": forecast}
