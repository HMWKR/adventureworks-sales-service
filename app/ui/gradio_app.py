# gradio_app.py — Gradio 대시보드 (FastAPI에 mount)
# ------------------------------------------------------------
# week11 main_gradio_mount.py 패턴: 서비스 함수를 직접 호출하는 gr.Blocks 를
# 구성하고, main.py 에서 gr.mount_gradio_app 으로 FastAPI 에 마운트한다.
# 5개 탭: EDA / RFM / 매출예측 / 세그먼트예측 / 시계열예측
# 디자인: 커스텀 CSS(그라데이션 헤더·KPI 카드·결과 카드) + 통화 포맷.
# ------------------------------------------------------------
import logging

import gradio as gr
import pandas as pd

from app import data_access
from app.services import eda_service, rfm_service, ml_service

logger = logging.getLogger("aw.ui")

# ── 디자인 토큰 / 커스텀 CSS ─────────────────────────────────
PRIMARY = "#3182f6"
CSS = """
/* ── Toss 테마: Gradio CSS 변수 전면 오버라이드 (모든 컴포넌트 상속) ── */
.gradio-container, .gradio-container.gradio-container {
  --body-background-fill: #f9fafb !important;
  --background-fill-primary: #ffffff !important;
  --background-fill-secondary: #f9fafb !important;
  --block-background-fill: #ffffff !important;
  --block-border-color: #f2f4f6 !important;
  --block-border-width: 1px !important;
  --block-radius: 18px !important;
  --block-label-background-fill: #ffffff !important;
  --block-label-text-color: #4e5968 !important;
  --block-title-text-color: #191f28 !important;
  --block-shadow: 0 1px 2px rgba(0,0,0,.04), 0 4px 16px rgba(0,0,0,.05) !important;
  --body-text-color: #191f28 !important;
  --body-text-color-subdued: #8b95a1 !important;
  --input-background-fill: #ffffff !important;
  --input-border-color: #e5e8eb !important;
  --input-border-color-focus: #3182f6 !important;
  --input-radius: 12px !important;
  --button-large-radius: 14px !important;
  --button-small-radius: 12px !important;
  --button-primary-background-fill: #3182f6 !important;
  --button-primary-background-fill-hover: #1b64da !important;
  --button-primary-text-color: #ffffff !important;
  --button-secondary-background-fill: #ffffff !important;
  --button-secondary-border-color: #e5e8eb !important;
  --color-accent: #3182f6 !important;
  --color-accent-soft: #eef5ff !important;
  --primary-50:#eef5ff !important; --primary-500: #3182f6 !important; --primary-600: #1b64da !important;
  --link-text-color: #3182f6 !important; --link-text-color-hover: #1b64da !important;
  --layout-gap: 16px !important;
  font-family: 'Pretendard','Toss Product Sans','Segoe UI','Malgun Gothic',sans-serif !important;
  max-width: 1080px !important; margin: 0 auto !important;
  background: #f9fafb !important;
}
/* primary 버튼 */
.gradio-container .primary, .gradio-container button.primary {
  background: #3182f6 !important; color:#fff !important; font-weight:700 !important;
  border:none !important; border-radius:14px !important; box-shadow:none !important;
}
.gradio-container .primary:hover, .gradio-container button.primary:hover { background:#1b64da !important; }
/* 탭 네비 → Toss 세그먼트 컨트롤 느낌 */
.gradio-container .tab-nav, .gradio-container div[role="tablist"] {
  border:none !important; gap:4px !important; background:#f2f4f6 !important;
  padding:5px !important; border-radius:14px !important; display:inline-flex !important;
}
.gradio-container .tab-nav button, .gradio-container button[role="tab"] {
  border:none !important; border-radius:10px !important; color:#4e5968 !important;
  font-weight:700 !important; padding:9px 16px !important; background:transparent !important;
}
.gradio-container .tab-nav button.selected, .gradio-container button[role="tab"][aria-selected="true"] {
  background:#fff !important; color:#3182f6 !important;
  box-shadow:0 1px 3px rgba(0,0,0,.08) !important;
}
/* 입력/드롭다운 */
.gradio-container input, .gradio-container select, .gradio-container textarea {
  border-radius:12px !important; }
.gradio-container label span, .gradio-container .block-title {
  color:#4e5968 !important; font-weight:600 !important; }
.gradio-container .block { box-shadow: var(--block-shadow) !important; }

/* ── 커스텀 히어로 / KPI / 결과 카드 (Toss) ── */
#aw-hero { background: linear-gradient(120deg,#3182f6 0%,#1b64da 100%);
  color:#fff; padding:26px 30px; border-radius:20px; margin-bottom:6px;
  box-shadow:0 10px 30px rgba(49,130,246,.22); }
#aw-hero h1 { margin:0; font-size:1.7rem; font-weight:800; letter-spacing:-.02em; color:#fff; }
#aw-hero .sub { opacity:.92; margin-top:4px; font-size:.95rem; }
.kpi-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr));
  gap:12px; margin-top:18px; }
.kpi { background:rgba(255,255,255,.16); backdrop-filter:blur(4px);
  border:1px solid rgba(255,255,255,.24); border-radius:14px; padding:13px 15px; }
.kpi .num { font-size:1.45rem; font-weight:800; line-height:1.1; }
.kpi .label { font-size:.78rem; opacity:.9; margin-top:3px; }
.result-card { border-radius:18px; padding:24px 26px; margin-top:4px;
  background:linear-gradient(135deg,#eef5ff,#f9fafb); border:1.5px solid #d6e6ff; }
.result-card .big { font-size:2.4rem; font-weight:800; color:#1b64da; letter-spacing:-.02em; }
.result-card .lbl { color:#4e5968; font-size:.9rem; font-weight:700; }
.seg-badge { display:inline-block; padding:8px 20px; border-radius:999px;
  font-weight:800; font-size:1.3rem; background:#3182f6; color:#fff; }
.section-title { font-weight:700; font-size:1.05rem; margin:6px 0 2px; }
footer { display:none !important; }
"""


def _won(v: float) -> str:
    return f"${v:,.2f}"


def _human(v: float) -> str:
    """큰 숫자를 K/M 단위로 축약."""
    if abs(v) >= 1_000_000:
        return f"{v/1_000_000:.1f}M"
    if abs(v) >= 1_000:
        return f"{v/1_000:.1f}K"
    return f"{v:,.0f}"


# ── 드롭다운 선택지(실데이터에서 추출) ───────────────────────
def _choices():
    df = data_access.get_dataframe()
    cats = sorted(df["Category"].dropna().unique().tolist())
    subs = sorted(df["Subcategory"].dropna().unique().tolist())
    regions = sorted(df["Region"].dropna().unique().tolist())
    channels = sorted(df["Channel"].dropna().unique().tolist())
    return cats, subs, regions, channels


# ── 예측 핸들러 ──────────────────────────────────────────────
def _predict_sales(qty, list_price, std_cost, category, subcategory, channel, region):
    try:
        r = ml_service.predict_sales(int(qty), float(list_price), float(std_cost),
                                     category, subcategory, channel, region)
        return (f"<div class='result-card'><div class='lbl'>💰 예측 매출액</div>"
                f"<div class='big'>{_won(r['predicted_sales_amount'])}</div></div>")
    except ml_service.InvalidInput as e:
        return f"<div class='result-card'>⚠️ 입력 오류: {e}</div>"
    except Exception as e:
        logger.exception("predict_sales 실패")
        return f"<div class='result-card'>❌ 예측 오류: {e}</div>"


def _predict_segment(recency, frequency, monetary):
    try:
        r = ml_service.classify_segment(int(recency), int(frequency), float(monetary))
        prob_df = pd.DataFrame(
            [{"segment": k, "probability": round(v, 4)} for k, v in r["probabilities"].items()]
        )
        html = (f"<div class='result-card'><div class='lbl'>🎯 예측 세그먼트</div>"
                f"<div style='margin:10px 0'><span class='seg-badge'>{r['segment']}</span></div>"
                f"<div class='lbl'>확신도 {r['confidence']*100:.1f}%</div></div>")
        return html, prob_df
    except Exception as e:
        logger.exception("predict_segment 실패")
        return f"<div class='result-card'>❌ 예측 오류: {e}</div>", pd.DataFrame()


def _forecast(horizon):
    try:
        r = ml_service.forecast_monthly(int(horizon))
        hist = pd.DataFrame(r["history"]).rename(columns={"sales_amount": "value"})
        hist["type"] = "실제"
        fc = pd.DataFrame(r["forecast"]).rename(columns={"forecast_sales_amount": "value"})
        fc["type"] = "예측"
        combined = pd.concat([hist[["month", "value", "type"]],
                              fc[["month", "value", "type"]]], ignore_index=True)
        combined["month"] = pd.to_datetime(combined["month"])   # 시간축(라벨 자동 간격)
        table = fc[["month", "value"]].rename(columns={"value": "예측 매출액($)"})
        table["예측 매출액($)"] = table["예측 매출액($)"].map(lambda x: f"{x:,.0f}")
        return combined, table
    except Exception as e:
        logger.exception("forecast 실패")
        return pd.DataFrame(), pd.DataFrame({"오류": [str(e)]})


def _hero_html(s: dict) -> str:
    kpis = [
        (f"${_human(s['total_sales'])}", "총매출"),
        (f"{s['total_orders']:,}", "주문 수"),
        (f"{s['total_quantity']:,}", "판매 수량"),
        (f"{s['unique_buyers']:,}", "구매자"),
        (f"{s['unique_products']:,}", "제품"),
        (f"{s['n_regions']}", "지역"),
    ]
    cards = "".join(
        f"<div class='kpi'><div class='num'>{v}</div><div class='label'>{l}</div></div>"
        for v, l in kpis
    )
    return (
        f"<style>{CSS}</style>"          # Gradio 6 mount 환경: css= 대신 style 태그 직접 주입
        "<div id='aw-hero'>"
        "<h1>🚲 AdventureWorks 매출 분석·예측 서비스</h1>"
        f"<div class='sub'>CRISP-DM 파이프라인 · EDA · RFM · 매출회귀 · 고객분류 · 시계열예측 "
        f"&nbsp;|&nbsp; 기간 {s['date_from']} ~ {s['date_to']}</div>"
        f"<div class='kpi-grid'>{cards}</div>"
        "</div>"
    )


# ── Blocks 구성 ──────────────────────────────────────────────
def build_demo() -> gr.Blocks:
    cats, subs, regions, channels = _choices()
    s = eda_service.summary()

    monthly_df = pd.DataFrame(eda_service.monthly_sales())
    region_df = pd.DataFrame(eda_service.region_sales())
    category_df = pd.DataFrame(eda_service.category_sales())
    channel_df = pd.DataFrame(eda_service.channel_sales())
    seg_df = pd.DataFrame(rfm_service.segment_summary())
    top_df = pd.DataFrame(rfm_service.top_customers(20))[
        ["Buyer", "Recency", "Frequency", "Monetary", "RFM_Score", "Segment"]]

    with gr.Blocks(title="AdventureWorks 매출 분석·예측") as demo:
        gr.HTML(_hero_html(s))

        # ── EDA ──
        with gr.Tab("📊 EDA 분석"):
            gr.Markdown("월별 추이와 지역·카테고리·채널별 매출 분포를 살펴봅니다.")
            monthly_plot = monthly_df.assign(date=pd.to_datetime(monthly_df["YearMonth"]))
            gr.LinePlot(monthly_plot, x="date", y="sales_amount",
                        title="월별 매출 추이", height=300)
            with gr.Row():
                gr.BarPlot(region_df, x="Region", y="sales_amount",
                           title="지역별 매출", height=300)
                gr.BarPlot(category_df, x="Category", y="sales_amount",
                           title="카테고리별 매출", height=300)
            with gr.Row():
                gr.BarPlot(channel_df, x="Channel", y="sales_amount",
                           title="채널별 매출", height=280)
                gr.Dataframe(monthly_df, label="월별 집계 데이터")

        # ── RFM ──
        with gr.Tab("👥 RFM 고객분석"):
            gr.Markdown("Recency·Frequency·Monetary 기반 고객 세그먼트 분포입니다.")
            with gr.Row():
                gr.BarPlot(seg_df, x="Segment", y="customers",
                           title="세그먼트별 고객 수", height=300)
                gr.BarPlot(seg_df, x="Segment", y="total_monetary",
                           title="세그먼트별 총 매출", height=300)
            gr.Dataframe(seg_df, label="세그먼트 요약")
            gr.Markdown("**Monetary 상위 우수 고객 20**")
            gr.Dataframe(top_df, label="우수 고객")

        # ── 매출 예측 (회귀) ──
        with gr.Tab("💰 매출 예측"):
            gr.Markdown("주문 정보를 입력하면 **매출액**을 회귀 모델(RandomForest)로 예측합니다.")
            with gr.Row():
                with gr.Column(scale=1):
                    qty = gr.Number(label="주문 수량", value=3, minimum=1)
                    list_price = gr.Number(label="정가 (List Price, $)", value=2000.0)
                    std_cost = gr.Number(label="표준원가 (Standard Cost, $)", value=1200.0)
                    category = gr.Dropdown(cats, label="카테고리",
                                           value="Bikes" if "Bikes" in cats else (cats[0] if cats else None))
                    subcategory = gr.Dropdown(subs, label="서브카테고리",
                                              value=subs[0] if subs else None)
                    channel = gr.Dropdown(channels, label="채널",
                                          value=channels[0] if channels else None)
                    region = gr.Dropdown(regions, label="지역",
                                         value=regions[0] if regions else None)
                    btn = gr.Button("매출 예측하기", variant="primary", size="lg")
                with gr.Column(scale=1):
                    out = gr.HTML()
            btn.click(_predict_sales,
                      [qty, list_price, std_cost, category, subcategory, channel, region],
                      out)

        # ── 세그먼트 예측 (분류) ──
        with gr.Tab("🎯 고객 세그먼트 예측"):
            gr.Markdown("고객의 **R(최근성)·F(빈도)·M(금액)**을 입력하면 세그먼트를 분류합니다.")
            with gr.Row():
                with gr.Column(scale=1):
                    recency = gr.Number(label="Recency (마지막 구매 후 일수)", value=30, minimum=0)
                    frequency = gr.Number(label="Frequency (구매 횟수)", value=5, minimum=0)
                    monetary = gr.Number(label="Monetary (총 구매액, $)", value=15000.0, minimum=0)
                    seg_btn = gr.Button("세그먼트 예측하기", variant="primary", size="lg")
                with gr.Column(scale=1):
                    seg_out = gr.HTML()
                    seg_prob = gr.BarPlot(x="segment", y="probability",
                                          title="세그먼트 확률 분포", height=260)
            seg_btn.click(_predict_segment, [recency, frequency, monetary],
                          [seg_out, seg_prob])

        # ── 시계열 예측 ──
        with gr.Tab("📈 시계열 예측"):
            gr.Markdown("향후 N개월 **월매출**을 Holt-Winters 모델로 예측합니다.")
            with gr.Row():
                horizon = gr.Slider(1, 24, value=6, step=1, label="예측 개월 수")
                fc_btn = gr.Button("예측 실행", variant="primary", size="lg")
            fc_plot = gr.LinePlot(x="month", y="value", color="type",
                                  title="실제 vs 예측 월매출", height=340)
            fc_table = gr.Dataframe(label="예측 결과")
            fc_btn.click(_forecast, [horizon], [fc_plot, fc_table])

        gr.HTML(
            "<div style='text-align:center;color:#94a3b8;font-size:.82rem;padding:18px'>"
            "<a href='/' style='color:#3182f6;font-weight:600'>← 스토리 대시보드</a>"
            "&nbsp;·&nbsp; FastAPI + Gradio · AdventureWorks Sales · 기말과제 "
            "&nbsp;·&nbsp; <a href='/docs' target='_blank' style='color:#6366f1'>API 문서(Swagger) →</a>"
            "</div>"
        )

    return demo
