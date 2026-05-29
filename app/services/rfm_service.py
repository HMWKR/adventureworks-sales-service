# rfm_service.py — RFM 분석 (Recency / Frequency / Monetary)
# ------------------------------------------------------------
# 노트북 AdventureSales_03_Basic_EDA 의 RFM 분석을 재현·확장한다.
#   - Recency  : 스냅샷 기준 마지막 구매 후 경과 일수 (작을수록 우수)
#   - Frequency: 고유 주문 수 (클수록 우수)
#   - Monetary : 총 구매 금액 (클수록 우수)
# 5분위 점수(qcut)로 R/F/M 점수를 매기고, 규칙 기반 세그먼트를 부여한다.
# ------------------------------------------------------------
import datetime as dt
from functools import lru_cache

import pandas as pd

from app import data_access


def _score_segment(r: int, f: int, m: int) -> str:
    """R/F/M 점수(1~5) 조합 → 세그먼트 라벨(규칙 기반)."""
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    if r >= 3 and f >= 3:
        return "Loyal"
    if r >= 4 and f <= 2:
        return "Potential Loyalist"
    if r <= 2 and f >= 3:
        return "At Risk"
    if r <= 2 and f <= 2 and m >= 3:
        return "Hibernating"
    if r <= 1 and f <= 1:
        return "Lost"
    return "Others"


@lru_cache(maxsize=1)
def compute_rfm() -> pd.DataFrame:
    """구매자(Buyer)별 RFM 테이블 + 점수 + 세그먼트 계산(캐시)."""
    df = data_access.get_dataframe()
    if df.empty:
        raise ValueError("입력 데이터가 비어 있어 RFM 을 계산할 수 없습니다.")
    snapshot = df["Date"].max() + dt.timedelta(days=1)

    rfm = df.groupby("Buyer").agg(
        Recency=("Date", lambda d: (snapshot - d.max()).days),
        Frequency=("Sales Order", "nunique"),
        Monetary=("Sales Amount", "sum"),
    ).reset_index()
    if rfm.empty:
        raise ValueError("RFM 계산 결과가 비어 있습니다.")
    rfm["Monetary"] = rfm["Monetary"].round(2)

    # 5분위 점수 (rank 로 동점 분산). 5분위로 나눌 만큼 데이터가 부족하면
    # (소규모/테스트 데이터) 중앙 점수 3으로 폴백한다.
    try:
        rfm["R_Score"] = pd.qcut(rfm["Recency"].rank(method="first"), 5,
                                 labels=[5, 4, 3, 2, 1]).astype(int)
        rfm["F_Score"] = pd.qcut(rfm["Frequency"].rank(method="first"), 5,
                                 labels=[1, 2, 3, 4, 5]).astype(int)
        rfm["M_Score"] = pd.qcut(rfm["Monetary"].rank(method="first"), 5,
                                 labels=[1, 2, 3, 4, 5]).astype(int)
    except ValueError:
        rfm["R_Score"] = rfm["F_Score"] = rfm["M_Score"] = 3

    rfm["RFM_Score"] = (rfm["R_Score"].astype(str)
                        + rfm["F_Score"].astype(str)
                        + rfm["M_Score"].astype(str))
    rfm["Segment"] = rfm.apply(
        lambda x: _score_segment(x["R_Score"], x["F_Score"], x["M_Score"]), axis=1
    )
    return rfm


def reset_cache() -> None:
    compute_rfm.cache_clear()


def segment_summary() -> list[dict]:
    """세그먼트별 고객 수·평균 RFM·총 매출."""
    rfm = compute_rfm()
    g = rfm.groupby("Segment").agg(
        customers=("Buyer", "size"),
        avg_recency=("Recency", "mean"),
        avg_frequency=("Frequency", "mean"),
        total_monetary=("Monetary", "sum"),
    ).reset_index().sort_values("total_monetary", ascending=False)
    for c in ["avg_recency", "avg_frequency"]:
        g[c] = g[c].round(1)
    g["total_monetary"] = g["total_monetary"].round(2)
    return g.to_dict(orient="records")


def top_customers(n: int = 20) -> list[dict]:
    """Monetary 기준 상위 고객."""
    rfm = compute_rfm().sort_values("Monetary", ascending=False).head(n)
    return rfm[["Buyer", "Recency", "Frequency", "Monetary",
                "RFM_Score", "Segment"]].to_dict(orient="records")


def lookup(buyer: str) -> dict | None:
    """특정 구매자의 RFM 조회."""
    rfm = compute_rfm()
    row = rfm[rfm["Buyer"] == buyer]
    if row.empty:
        return None
    r = row.iloc[0]
    return {
        "buyer": buyer,
        "recency": int(r["Recency"]),
        "frequency": int(r["Frequency"]),
        "monetary": float(r["Monetary"]),
        "rfm_score": r["RFM_Score"],
        "segment": r["Segment"],
    }
