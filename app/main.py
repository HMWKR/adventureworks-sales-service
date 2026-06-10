# main.py — FastAPI 앱 조립 + Gradio mount (Controller + 진입점)
# ------------------------------------------------------------
# - JSON API 라우터(eda/rfm/predict) 등록 + Swagger 자동 문서
# - Gradio 대시보드를 gr.mount_gradio_app 으로 "/" 에 마운트 (week11 패턴)
# - lifespan 에서 데이터/모델을 워밍업(없으면 ETL·학습 자동 트리거)
# 실행: uvicorn app.main:app --reload   →  http://127.0.0.1:8000/ (대시보드)
#                                          http://127.0.0.1:8000/docs (API)
# ------------------------------------------------------------
import os
from contextlib import asynccontextmanager

import gradio as gr
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import data_access
from app.services import ml_service
from app.routers import eda, rfm, predict, insights
from app.web.router import router as web_router
from app.ui.gradio_app import build_demo

_APP_DIR = os.path.dirname(os.path.abspath(__file__))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 데이터 + 모델 워밍업 (최초 1회 ETL/학습 자동 트리거)
    data_access.get_dataframe()
    ml_service._load()
    print("✅ 데이터·모델 준비 완료")
    yield


app = FastAPI(
    title="AdventureWorks 매출 분석·예측 API",
    description="CRISP-DM 파이프라인 + EDA/RFM + 매출회귀·고객분류·시계열 예측 (기말과제)",
    version="2.0.0",
    lifespan=lifespan,
)

# 정적 파일 (Toss CSS / ECharts JS)
app.mount("/static", StaticFiles(directory=os.path.join(_APP_DIR, "static")), name="static")

# JSON API 라우터 (/api 프리픽스)
app.include_router(eda.router, prefix="/api")
app.include_router(rfm.router, prefix="/api")
app.include_router(predict.router, prefix="/api")
app.include_router(insights.router, prefix="/api")

# 커스텀 스토리 대시보드 ("/")
app.include_router(web_router)


@app.get("/health", tags=["Meta"])
def health():
    return {"status": "ok"}


@app.get("/api/glossary", tags=["Meta"])
def glossary():
    """카테고리·채널·지역·세그먼트의 한국어 뜻·설명(용어집)."""
    from app import i18n
    return {"kinds": i18n.KIND_LABEL, "glossary": i18n.get_glossary()}


@app.get("/api", tags=["Meta"])
def api_index():
    """API 엔드포인트 안내."""
    return {
        "eda": ["/api/eda/summary", "/api/eda/monthly-sales", "/api/eda/region-sales",
                "/api/eda/category-sales", "/api/eda/channel-sales", "/api/eda/top-products"],
        "rfm": ["/api/rfm/segments", "/api/rfm/top-customers", "/api/rfm/customer/{buyer}"],
        "predict": ["/api/predict/sales (POST)", "/api/predict/segment (POST)",
                    "/api/predict/forecast"],
        "insights": ["/api/insights", "/api/insights/dashboard"],
        "ui": {"dashboard": "/", "playground": "/playground",
               "gradio": "/gradio", "docs": "/docs"},
    }


# Gradio 버전(강의 gr.mount_gradio_app 데모)을 "/gradio" 에 보존.
# 기본 플레이그라운드("/playground")와 대시보드("/")는 커스텀 Toss 페이지가 담당.
demo = build_demo()
app = gr.mount_gradio_app(app, demo, path="/gradio")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
