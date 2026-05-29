# web/router.py — 커스텀 스토리 대시보드 ("/")
# ------------------------------------------------------------
# 자동 인사이트 + 차트 데이터를 서버에서 조립해 Jinja2 템플릿에 주입한다.
# (ECharts 가 window.__DATA__ 로 즉시 렌더 → API 왕복 플래시 없음)
# ------------------------------------------------------------
import json
import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app import data_access
from app.services import insight_service

_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # app/
templates = Jinja2Templates(directory=os.path.join(_APP_DIR, "templates"))

router = APIRouter(tags=["Dashboard"])


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    payload = insight_service.build_dashboard_payload()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "data_json": json.dumps(payload, ensure_ascii=False),
        "s": payload["summary"],
        "sh": payload["summary_human"],
        "insights": payload["insights"],
    })


@router.get("/playground", response_class=HTMLResponse)
def playground(request: Request):
    """커스텀 Toss 디자인 예측 플레이그라운드 (폼 → /api/predict/* fetch)."""
    df = data_access.get_dataframe()
    choices = {
        "categories": sorted(df["Category"].dropna().unique().tolist()),
        "subcategories": sorted(df["Subcategory"].dropna().unique().tolist()),
        "channels": sorted(df["Channel"].dropna().unique().tolist()),
        "regions": sorted(df["Region"].dropna().unique().tolist()),
    }
    return templates.TemplateResponse("playground.html", {
        "request": request,
        "choices_json": json.dumps(choices, ensure_ascii=False),
    })
