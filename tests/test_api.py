# test_api.py — pytest API 테스트 (CRISP-DM 5단계: 테스트)
# ------------------------------------------------------------
# 실행:  pytest -q   (또는  python -m pytest tests/ -q)
# 데이터/모델이 없으면 lifespan 이 ETL·학습을 자동 트리거한다.
# ------------------------------------------------------------
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:   # lifespan 진입 → 데이터/모델 워밍업
        yield c


# ── 메타 ─────────────────────────────────────────────────────
def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_dashboard(client):
    # "/" 는 커스텀 스토리 대시보드(ECharts + 주입 데이터)
    r = client.get("/")
    assert r.status_code == 200
    assert "window.__DATA__" in r.text
    assert "echarts" in r.text.lower()


def test_static_assets(client):
    assert client.get("/static/css/toss.css").status_code == 200
    assert client.get("/static/js/dashboard.js").status_code == 200


def test_playground_custom(client):
    # /playground 는 커스텀 Toss 페이지(폼 → /api/predict/* fetch)
    r = client.get("/playground")
    assert r.status_code == 200
    assert "window.__CHOICES__" in r.text
    assert "playground.js" in r.text


def test_gradio_version(client):
    # 강의 요구 Gradio 버전은 /gradio 에 보존
    r = client.get("/gradio")
    assert r.status_code == 200
    assert "gradio" in r.text.lower()


def test_insights(client):
    data = client.get("/api/insights").json()
    assert len(data) >= 3
    assert {"icon", "title", "metric", "text"} <= set(data[0])


def test_glossary(client):
    # 용어집(영→한 뜻) API — 카테고리/채널/지역/세그먼트
    g = client.get("/api/glossary").json()
    assert "glossary" in g and "kinds" in g
    gl = g["glossary"]
    assert {"category", "channel", "region", "segment"} <= set(gl)
    assert gl["category"]["Bikes"]["ko"] == "자전거"
    assert gl["channel"]["Reseller"]["ko"]  # 한국어 라벨 존재


def test_swagger(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200


# ── EDA ──────────────────────────────────────────────────────
def test_summary(client):
    s = client.get("/api/eda/summary").json()
    assert s["n_months"] == 36
    assert s["total_sales"] > 0
    assert s["unique_buyers"] > 1000


def test_monthly_sales(client):
    r = client.get("/api/eda/monthly-sales")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 36
    assert {"YearMonth", "sales_amount", "order_quantity"} <= set(data[0])
    # 시계열 순 정렬 확인
    months = [d["YearMonth"] for d in data]
    assert months == sorted(months)


def test_region_sales(client):
    data = client.get("/api/eda/region-sales").json()
    assert len(data) >= 5
    # 매출 내림차순 확인
    amts = [d["sales_amount"] for d in data]
    assert amts == sorted(amts, reverse=True)


def test_category_sales(client):
    data = client.get("/api/eda/category-sales").json()
    cats = {d["Category"] for d in data}
    assert "Bikes" in cats


# ── RFM ──────────────────────────────────────────────────────
def test_rfm_segments(client):
    data = client.get("/api/rfm/segments").json()
    assert len(data) >= 3
    assert {"Segment", "customers", "total_monetary"} <= set(data[0])


def test_rfm_top_customers(client):
    data = client.get("/api/rfm/top-customers?n=5").json()
    assert len(data) == 5
    # Monetary 내림차순
    monos = [d["monetary"] for d in data]
    assert monos == sorted(monos, reverse=True)


def test_rfm_customer_not_found(client):
    r = client.get("/api/rfm/customer/__no_such_buyer__")
    assert r.status_code == 404


# ── 예측: 회귀 ───────────────────────────────────────────────
def test_predict_sales(client):
    r = client.post("/api/predict/sales", json={
        "order_quantity": 3, "list_price": 2000, "standard_cost": 1200,
        "category": "Bikes", "subcategory": "Road Bikes",
        "channel": "Reseller", "region": "Southwest"})
    assert r.status_code == 200
    assert r.json()["predicted_sales_amount"] > 0


def test_predict_sales_validation(client):
    # order_quantity <= 0 → 422
    r = client.post("/api/predict/sales", json={
        "order_quantity": 0, "list_price": 2000, "standard_cost": 1200,
        "category": "Bikes", "subcategory": "Road Bikes",
        "channel": "Reseller", "region": "Southwest"})
    assert r.status_code == 422


def test_predict_sales_unknown_category(client):
    # 학습에 없던 범주값 → 400 (unknown OHE 무시로 인한 잘못된 예측 차단)
    r = client.post("/api/predict/sales", json={
        "order_quantity": 3, "list_price": 2000, "standard_cost": 1200,
        "category": "스페이스선박", "subcategory": "Road Bikes",
        "channel": "Reseller", "region": "Southwest"})
    assert r.status_code == 400


# ── 예측: 분류 ───────────────────────────────────────────────
def test_predict_segment(client):
    r = client.post("/api/predict/segment",
                    json={"recency": 30, "frequency": 5, "monetary": 15000})
    assert r.status_code == 200
    body = r.json()
    assert body["segment"]
    assert 0 <= body["confidence"] <= 1
    # 확률 합 ≈ 1
    assert abs(sum(body["probabilities"].values()) - 1.0) < 0.01


def test_predict_segment_high_value(client):
    # 최근·고빈도·고액 → Champions 계열 기대
    r = client.post("/api/predict/segment",
                    json={"recency": 5, "frequency": 12, "monetary": 500000}).json()
    assert r["segment"] in ("Champions", "Loyal")


# ── 예측: 구매 Buy or Not (과제 5-1, CRM) ────────────────────
def test_predict_buy(client):
    r = client.post("/api/predict/buy", json={
        "region": "Southwest", "channel": "Reseller", "category": "Bikes",
        "prior_orders": 8, "prior_monetary": 200000})
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"will_buy", "label", "buy_probability"}
    assert 0 <= body["buy_probability"] <= 1
    assert isinstance(body["will_buy"], bool)


def test_predict_buy_active_vs_inactive(client):
    # 활성 고객(구매 多)은 비활성 고객보다 구매 확률이 높아야 함
    active = client.post("/api/predict/buy", json={
        "region": "Southwest", "channel": "Reseller", "category": "Bikes",
        "prior_orders": 10, "prior_monetary": 300000}).json()
    inactive = client.post("/api/predict/buy", json={
        "region": "Australia", "channel": "Internet", "category": "Bikes",
        "prior_orders": 1, "prior_monetary": 50}).json()
    assert active["buy_probability"] > inactive["buy_probability"]


def test_predict_buy_unknown_region(client):
    r = client.post("/api/predict/buy", json={
        "region": "행성X", "channel": "Reseller", "category": "Bikes"})
    assert r.status_code == 400


# ── 예측: 시계열 ─────────────────────────────────────────────
def test_forecast(client):
    r = client.get("/api/predict/forecast?horizon=6")
    assert r.status_code == 200
    body = r.json()
    assert body["horizon"] == 6
    assert len(body["history"]) == 36
    assert len(body["forecast"]) == 6
    assert all(p["forecast_sales_amount"] > 0 for p in body["forecast"])


def test_forecast_validation(client):
    # horizon > 24 → 422
    assert client.get("/api/predict/forecast?horizon=99").status_code == 422
