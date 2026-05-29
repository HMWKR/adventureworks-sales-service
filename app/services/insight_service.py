# insight_service.py — 자동 인사이트 생성 + 대시보드 페이로드 조립
# ------------------------------------------------------------
# 집계/RFM/예측 결과로부터 "사람이 읽는 한 문장 인사이트"를 자동 생성하고,
# 스토리 대시보드가 쓸 차트 데이터 번들을 한 번에 조립한다(서버 주입용).
# ------------------------------------------------------------
from app import data_access
from app.services import eda_service, rfm_service, ml_service


def _pct(n: float, d: float) -> float:
    return round(n / d * 100, 1) if d else 0.0


def generate_insights() -> list[dict]:
    """대시보드 상단에 노출할 핵심 내러티브 인사이트(자동)."""
    summ = eda_service.summary()
    monthly = eda_service.monthly_sales()
    regions = eda_service.region_sales()
    cats = eda_service.category_sales()
    segs = rfm_service.segment_summary()
    total = summ["total_sales"] or 1

    out: list[dict] = []

    # 1) 연간 성장 (최근 12개월 vs 직전 12개월)
    vals = [m["sales_amount"] for m in monthly]
    if len(vals) >= 24:
        last12, prev12 = sum(vals[-12:]), sum(vals[-24:-12])
        g = _pct(last12 - prev12, prev12)
        out.append({
            "icon": "📈", "title": "연간 성장세",
            "metric": f"{g:+.1f}%", "tone": "up" if g >= 0 else "down",
            "text": f"최근 12개월 매출이 직전 12개월 대비 {g:+.1f}% "
                    f"{'성장했어요' if g >= 0 else '감소했어요'}.",
        })

    # 2) 핵심 카테고리 집중도
    if cats:
        c = cats[0]
        share = _pct(c["sales_amount"], total)
        out.append({
            "icon": "🏆", "title": "매출 1위 카테고리",
            "metric": f"{share:.0f}%", "tone": "neutral",
            "text": f"'{c['Category']}'가 전체 매출의 {share:.0f}%를 차지하는 핵심 동력이에요.",
        })

    # 3) 지역 1위
    if regions:
        r = regions[0]
        share = _pct(r["sales_amount"], total)
        out.append({
            "icon": "📍", "title": "최대 매출 지역",
            "metric": r["Region"], "tone": "neutral",
            "text": f"'{r['Region']}' 지역이 매출 1위로 전체의 {share:.0f}%를 만들어요.",
        })

    # 4) 핵심 고객 세그먼트 기여
    if segs:
        top = segs[0]
        share = _pct(top["total_monetary"], total)
        out.append({
            "icon": "👑", "title": "핵심 고객층",
            "metric": f"{top['customers']:,}명", "tone": "up",
            "text": f"'{top['Segment']}' {top['customers']:,}명이 전체 매출의 "
                    f"{share:.0f}%를 책임지는 우량 고객이에요.",
        })

    # 5) 미래 전망 (향후 6개월 평균 vs 최근 6개월 평균)
    try:
        fc = ml_service.forecast_monthly(6)
        future = [p["forecast_sales_amount"] for p in fc["forecast"]]
        recent = [p["sales_amount"] for p in fc["history"][-6:]]
        if future and recent:
            fa, ra = sum(future) / len(future), sum(recent) / len(recent)
            g = _pct(fa - ra, ra)
            out.append({
                "icon": "🔮", "title": "향후 6개월 전망",
                "metric": f"${fa/1_000_000:.1f}M", "tone": "up" if g >= 0 else "down",
                "text": f"향후 6개월 월평균 매출은 ${fa/1_000_000:.1f}M, 최근 6개월 대비 "
                        f"{g:+.1f}% 수준으로 전망돼요.",
            })
    except Exception:
        pass

    return out


def _humanize(v: float) -> str:
    if abs(v) >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    if abs(v) >= 1_000:
        return f"${v/1_000:.0f}K"
    return f"${v:,.0f}"


def build_dashboard_payload() -> dict:
    """스토리 대시보드(서버 주입용) 전체 데이터 번들."""
    summ = eda_service.summary()
    monthly = eda_service.monthly_sales()
    cats = eda_service.category_sales()
    regions = eda_service.region_sales()
    channels = eda_service.channel_sales()
    top_products = eda_service.top_products(10)
    segs = rfm_service.segment_summary()
    fc = ml_service.forecast_monthly(6)

    return {
        "summary": summ,
        "summary_human": {
            "total_sales": _humanize(summ["total_sales"]),
            "avg_order_value": _humanize(summ["avg_order_value"]),
        },
        "insights": generate_insights(),
        "charts": {
            "monthly": monthly,
            "category": cats,
            "region": regions,
            "channel": channels,
            "top_products": top_products,
            "segments": segs,
            "forecast": fc,
        },
    }
