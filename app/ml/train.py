# train.py — ML 모델 학습 (CRISP-DM 4단계: 모델링)
# ------------------------------------------------------------
# 4개 모델을 학습·저장한다.
#   1) 매출 회귀     : Sales Amount 예측 (RandomForestRegressor)   [과제 5-2]
#   2) 구매 예측     : Buy or Not Buy 분류 (RandomForestClassifier) [과제 5-1, CRM]
#   3) 고객 분류     : RFM 세그먼트 분류 (RandomForestClassifier)   [보너스]
#   4) 월매출 시계열 : Holt-Winters 지수평활 (statsmodels)          [보너스]
# 산출물: models/*.pkl + models/metrics.json
# ------------------------------------------------------------
import json
import pickle
import datetime as dt

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, f1_score, classification_report, roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from app import config, data_access
from app.services import rfm_service


# ── 1. 매출 회귀 ─────────────────────────────────────────────
def train_sales_regressor(df: pd.DataFrame) -> dict:
    feats = config.REG_NUM_FEATURES + config.REG_CAT_FEATURES
    data = df.dropna(subset=feats + [config.REG_TARGET]).copy()
    X = data[feats]
    y = data[config.REG_TARGET]

    pre = ColumnTransformer([
        ("num", "passthrough", config.REG_NUM_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore"), config.REG_CAT_FEATURES),
    ])
    model = Pipeline([
        ("pre", pre),
        ("rf", RandomForestRegressor(
            n_estimators=80, max_depth=18, n_jobs=-1,
            random_state=config.RANDOM_STATE)),
    ])

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=config.RANDOM_STATE)
    model.fit(X_tr, y_tr)
    pred = model.predict(X_te)

    # 추론 시 unknown 범주 입력 검증을 위해 학습에 등장한 범주값을 저장
    cat_values = {c: sorted(map(str, data[c].dropna().unique().tolist()))
                  for c in config.REG_CAT_FEATURES}
    with open(config.REG_MODEL, "wb") as f:
        pickle.dump({"model": model, "features": feats,
                     "num": config.REG_NUM_FEATURES,
                     "cat": config.REG_CAT_FEATURES,
                     "cat_values": cat_values}, f)

    metrics = {
        "n_train": int(len(X_tr)), "n_test": int(len(X_te)),
        "r2": round(float(r2_score(y_te, pred)), 4),
        "mae": round(float(mean_absolute_error(y_te, pred)), 2),
        "rmse": round(float(np.sqrt(mean_squared_error(y_te, pred))), 2),
        "features": feats,
    }
    print(f"  [회귀] R²={metrics['r2']}  MAE={metrics['mae']}  RMSE={metrics['rmse']}")
    return metrics


# ── 2. 구매 예측 (Buy or Not Buy) — 고객×상품 카테고리 성향 [과제 5-1] ──
def train_buy_classifier(df: pd.DataFrame) -> dict:
    """CRM 핵심: 어떤 고객이 어떤 상품(카테고리)을 구매하는지 Buy/Not 분류.

    거래 데이터는 구매(positive)만 있으므로, 구매자×카테고리 전체 격자를 만들고
    실제 구매한 조합을 1, 나머지를 0(negative sampling)으로 라벨링한다.
    피처: 고객의 과거 구매횟수·금액 + 지역·채널 + 대상 카테고리.
    """
    def _mode(s):
        s = s.dropna()
        return s.mode().iloc[0] if not s.empty else "Unknown"

    # 구매자 단위 집계(과거 행동 + 지역·채널)
    buyer = df.groupby("Buyer").agg(
        Region=("Region", _mode),
        Channel=("Channel", "first"),
        prior_orders=("Sales Order", "nunique"),
        prior_monetary=("Sales Amount", "sum"),
    ).reset_index()

    cats = sorted(df["Category"].dropna().unique().tolist())
    bought = set(map(tuple, df[["Buyer", "Category"]].dropna().drop_duplicates().values))

    # 구매자 × 카테고리 격자 → 라벨(실구매=1, 미구매=0)
    grid = buyer.loc[buyer.index.repeat(len(cats))].reset_index(drop=True)
    grid["Category"] = cats * len(buyer)
    grid["label"] = [int((b, c) in bought) for b, c in zip(grid["Buyer"], grid["Category"])]

    feats = config.BUY_NUM_FEATURES + config.BUY_CAT_FEATURES
    X, y = grid[feats], grid["label"]
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=config.RANDOM_STATE, stratify=y)

    pre = ColumnTransformer([
        ("num", "passthrough", config.BUY_NUM_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore"), config.BUY_CAT_FEATURES),
    ])
    model = Pipeline([
        ("pre", pre),
        ("rf", RandomForestClassifier(
            n_estimators=120, max_depth=16, n_jobs=-1,
            random_state=config.RANDOM_STATE, class_weight="balanced")),
    ])
    model.fit(X_tr, y_tr)
    pred = model.predict(X_te)
    proba = model.predict_proba(X_te)[:, 1]

    cat_values = {c: sorted(map(str, grid[c].dropna().unique().tolist()))
                  for c in config.BUY_CAT_FEATURES}
    with open(config.BUY_MODEL, "wb") as f:
        pickle.dump({"model": model, "features": feats,
                     "num": config.BUY_NUM_FEATURES, "cat": config.BUY_CAT_FEATURES,
                     "cat_values": cat_values, "categories": cats}, f)

    metrics = {
        "n_train": int(len(X_tr)), "n_test": int(len(X_te)),
        "positives": int(y.sum()), "negatives": int((y == 0).sum()),
        "accuracy": round(float(accuracy_score(y_te, pred)), 4),
        "f1": round(float(f1_score(y_te, pred)), 4),
        "roc_auc": round(float(roc_auc_score(y_te, proba)), 4),
        "features": feats,
    }
    print(f"  [구매예측] accuracy={metrics['accuracy']}  F1={metrics['f1']}  "
          f"ROC-AUC={metrics['roc_auc']}  (pos {metrics['positives']:,}/neg {metrics['negatives']:,})")
    return metrics


# ── 3. 고객 RFM 세그먼트 분류 (보너스) ───────────────────────
def train_segment_classifier() -> dict:
    rfm = rfm_service.compute_rfm()
    X = rfm[["Recency", "Frequency", "Monetary"]]
    y = rfm["Segment"]

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=config.RANDOM_STATE, stratify=y)
    # max_depth 제한: 3개 수치 피처라 깊은 트리는 과대(모델 용량↑)·과적합 유발.
    clf = RandomForestClassifier(
        n_estimators=100, max_depth=12, n_jobs=-1,
        random_state=config.RANDOM_STATE, class_weight="balanced")
    clf.fit(X_tr, y_tr)
    pred = clf.predict(X_te)

    with open(config.CLF_MODEL, "wb") as f:
        pickle.dump({"model": clf, "features": ["Recency", "Frequency", "Monetary"],
                     "classes": list(clf.classes_)}, f)

    metrics = {
        "n_train": int(len(X_tr)), "n_test": int(len(X_te)),
        "accuracy": round(float(accuracy_score(y_te, pred)), 4),
        "macro_f1": round(float(f1_score(y_te, pred, average="macro")), 4),
        "classes": list(clf.classes_),
        "report": classification_report(y_te, pred, output_dict=True, zero_division=0),
    }
    print(f"  [분류] accuracy={metrics['accuracy']}  macro_F1={metrics['macro_f1']}")
    return metrics


# ── 3. 월매출 시계열 (Holt-Winters) ──────────────────────────
def _fit_holt_winters(values):
    """가법 추세(damped) + 가법 계절(연 12개월) Holt-Winters 적합."""
    return ExponentialSmoothing(
        values, trend="add", damped_trend=True, seasonal="add",
        seasonal_periods=config.SEASONAL_PERIODS,
        initialization_method="estimated",
    ).fit()


def _safe_mape(actual, pred) -> float:
    """0 나눗셈을 방지한 MAPE(%). 분모를 max(|actual|, 1)로 보정."""
    actual = np.asarray(actual, dtype=float)
    pred = np.asarray(pred, dtype=float)
    denom = np.maximum(np.abs(actual), 1.0)
    return float(np.mean(np.abs((actual - pred) / denom)) * 100)


def train_monthly_forecaster(df: pd.DataFrame) -> dict:
    monthly = (df.groupby("YearMonth")["Sales Amount"].sum().sort_index())
    series = monthly.astype(float)
    idx = list(series.index)
    values = series.values

    # 계절성 학습에 필요한 최소 데이터(2 사이클) 검증
    if len(values) < config.SEASONAL_PERIODS * 2:
        raise ValueError(
            f"시계열 데이터 부족: {len(values)}개월 < 계절주기×2"
            f"({config.SEASONAL_PERIODS * 2}). 시계열 모델 학습 불가."
        )

    # 백테스트: 마지막 H개월을 holdout 으로 떼어 실제 미래 예측력 평가
    h = config.FORECAST_HORIZON
    test_metrics = {}
    if len(values) > config.SEASONAL_PERIODS + h:
        bt = _fit_holt_winters(values[:-h])
        bt_fc = np.asarray(bt.forecast(h), dtype=float)
        test_metrics = {
            "backtest_mae": round(float(mean_absolute_error(values[-h:], bt_fc)), 2),
            "backtest_rmse": round(float(np.sqrt(mean_squared_error(values[-h:], bt_fc))), 2),
            "backtest_mape_pct": round(_safe_mape(values[-h:], bt_fc), 2),
        }

    # 최종 서빙 모델: 전체 데이터로 재학습
    fit = _fit_holt_winters(values)
    in_sample = fit.fittedvalues
    forecast = fit.forecast(h)

    with open(config.TS_MODEL, "wb") as f:
        pickle.dump({"fit": fit, "index": idx, "values": values.tolist(),
                     "horizon": h}, f)

    metrics = {
        "n_months": int(len(values)),
        "seasonal_periods": config.SEASONAL_PERIODS,
        "in_sample_mae": round(float(mean_absolute_error(values, in_sample)), 2),
        "in_sample_rmse": round(float(np.sqrt(mean_squared_error(values, in_sample))), 2),
        "in_sample_mape_pct": round(_safe_mape(values, in_sample), 2),
        **test_metrics,
        "horizon": h,
        "forecast_preview": [round(float(v), 2) for v in forecast[:3]],
    }
    bt_mape = metrics.get("backtest_mape_pct", "-")
    print(f"  [시계열] in-MAPE={metrics['in_sample_mape_pct']}%  backtest-MAPE={bt_mape}%")
    return metrics


# ── 전체 학습 ────────────────────────────────────────────────
def train_all() -> dict:
    print("🎯 모델 학습 시작...")
    df = data_access.get_dataframe()
    rfm_service.reset_cache()

    metrics = {
        "trained_at": dt.datetime.now().isoformat(timespec="seconds"),
        "dataset_rows": int(len(df)),
        "regression": train_sales_regressor(df),
        "buy_classification": train_buy_classifier(df),
        "classification": train_segment_classifier(),
        "timeseries": train_monthly_forecaster(df),
    }
    with open(config.METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    # 새로 학습한 모델이 즉시 서빙되도록 추론 캐시 무효화
    from app.services import ml_service
    ml_service.reset_cache()

    print(f"✅ 학습 완료 → {config.METRICS_JSON.name}")
    return metrics


if __name__ == "__main__":
    train_all()
