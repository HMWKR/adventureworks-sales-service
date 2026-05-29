# 🚲 AdventureWorks 매출 분석·예측 서비스 (기말과제)

`week13 FastAPI-MVC.pptx` 슬라이드 18~19의 **기말과제(CRISP-DM 적용)** 를 실제 동작 서비스로 구현한 프로젝트.
Microsoft **AdventureWorks Sales** 데이터를 ETL → 전처리 → EDA/RFM → 머신러닝(회귀·분류·시계열) → **FastAPI + Gradio** 서비스로 연결한다.

> 📖 상세 사용법은 [USER_GUIDE.md](USER_GUIDE.md) 참조.

## ✨ 핵심 기능

| 구분 | 내용 |
|---|---|
| **데이터** | MS Power BI `AdventureWorks Sales.xlsx`(7시트) 자동 다운로드 → 병합·전처리(121,253행, 36개월) → SQLite |
| **EDA** | 월별·지역별·카테고리별·채널별 매출 집계 |
| **RFM** | 구매자별 Recency/Frequency/Monetary 점수·세그먼트(Champions/Loyal/At Risk/Lost 등) |
| **ML 회귀** | 매출액 예측 — RandomForestRegressor (R² 0.98) |
| **ML 분류** | 고객 RFM 세그먼트 분류 — RandomForestClassifier (acc 0.76) |
| **ML 시계열** | 월매출 예측 — Holt-Winters(damped+가법계절), backtest-MAPE 21.5% |
| **UI** | ① 스토리 대시보드(`/`, Jinja2+ECharts+Toss 디자인, 자동 인사이트) ② 예측 플레이그라운드(`/playground`, 커스텀 Toss) ③ Gradio 버전(`/gradio`, Toss 테마 `gr.mount_gradio_app`) ④ Swagger(`/docs`) |

## 🧭 CRISP-DM 단계 매핑 (PPT 슬라이드 19)

| CRISP-DM | 구현 |
|---|---|
| 1. 비즈니스/데이터 이해 | `etl.py` 다운로드·시트 분석, `eda_service` 집계 |
| 2. 데이터 준비 | `etl.py` 7시트 병합·정제·통합 Buyer, `data_access` 캐시 |
| 3. 모델링 | `ml/train.py` 회귀·분류·시계열 학습 |
| 4. 평가 | `metrics.json`(R²/MAE/RMSE/accuracy/F1/MAPE + 시계열 backtest) |
| 5. 배포 | `main.py` FastAPI + Gradio mount, `tests/` pytest |

## 📁 구조 (MVC + 레이어드)

```
adventureworks_sales_service/
├── app/
│   ├── config.py            # 경로·상수
│   ├── etl.py               # 추출·변환·적재 (다운로드→병합→정제→SQLite/CSV)
│   ├── data_access.py       # 전처리 데이터 캐시 로더
│   ├── schemas.py           # Pydantic 입출력 (View)
│   ├── services/            # 비즈니스 로직 (Model)
│   │   ├── eda_service.py   #   집계
│   │   ├── rfm_service.py   #   RFM 분석·세그먼트
│   │   ├── ml_service.py    #   모델 로드·추론
│   │   └── insight_service.py  # 자동 인사이트 + 대시보드 페이로드
│   ├── ml/train.py          # 모델 학습 파이프라인
│   ├── routers/             # API 엔드포인트 (Controller)
│   │   ├── eda.py / rfm.py / predict.py / insights.py
│   ├── web/router.py        # 스토리 대시보드(/) + 플레이그라운드(/playground)
│   ├── templates/           # Jinja2: dashboard.html / playground.html
│   ├── static/              # Toss CSS + ECharts JS (dashboard.js / playground.js)
│   ├── ui/gradio_app.py     # Gradio 버전 (Toss 테마, /gradio)
│   └── main.py              # 앱 조립 + 라우터 + static + Gradio mount + lifespan
├── tests/test_api.py        # pytest 17케이스
├── run_pipeline.py          # ETL + 학습 일괄 실행
├── models/metrics.json      # 학습 지표(커밋)
└── requirements.txt
```

| MVC | 파일 |
|---|---|
| **Model** | `services/*` + `ml/train.py` + `etl.py` |
| **View** | `schemas.py` + `ui/gradio_app.py` + Swagger |
| **Controller** | `routers/*` + `main.py` |

## 🚀 빠른 시작

```bash
cd adventureworks_sales_service
pip install -r requirements.txt

# (선택) ETL + 모델 학습을 미리 실행 — 생략 시 첫 서버 기동에서 자동 수행
python run_pipeline.py

# 서버 실행
uvicorn app.main:app --reload
```

| 접속 | 주소 | 설명 |
|---|---|---|
| 스토리 대시보드 | http://127.0.0.1:8000/ | 자동 인사이트 + ECharts 시각화 (Toss 디자인) |
| 예측 플레이그라운드 | http://127.0.0.1:8000/playground | 매출·세그먼트·시계열 예측 (커스텀 Toss) |
| Gradio 버전 | http://127.0.0.1:8000/gradio | 강의 `gr.mount_gradio_app` 데모 (Toss 테마) |
| API 문서(Swagger) | http://127.0.0.1:8000/docs | REST API 자동 문서 |

> 첫 실행 시 `data/AdventureWorks_Sales.xlsx`(약 14MB)를 자동 다운로드하고 모델을 학습한다(수십 초~수 분). 대용량 산출물(xlsx/db/csv/pkl)은 `.gitignore` 처리되어 재생성된다.

## 🔌 주요 API (PPT 요구 + 확장)

| Method | URL | 설명 |
|---|---|---|
| GET | `/api/eda/monthly-sales` | 월별 매출 (PPT 요구) |
| GET | `/api/eda/region-sales` | 지역별 매출 (PPT 요구) |
| GET | `/api/eda/category-sales`, `/channel-sales`, `/top-products`, `/summary` | EDA 확장 |
| GET | `/api/rfm/segments`, `/top-customers`, `/customer/{buyer}` | RFM |
| POST | `/api/predict/sales` | 매출 회귀 예측 (PPT 요구) |
| POST | `/api/predict/segment` | 고객 세그먼트 분류 |
| GET | `/api/predict/forecast?horizon=N` | 월매출 시계열 예측 |

## 🧪 테스트

```bash
pytest -q          # 17 케이스: EDA·RFM·예측 3종·검증(422/400)·Gradio·Swagger
```

## 📊 모델 성능 (models/metrics.json)

| 모델 | 지표 |
|---|---|
| 매출 회귀 | R²=0.981, MAE=21.83, RMSE=234.28 |
| 세그먼트 분류 | accuracy=0.762, macro-F1=0.744 |
| 월매출 시계열 | in-sample MAPE=27.5%, **backtest MAPE=21.5%** |

> **세그먼트 분류 참고**: 라벨(세그먼트)은 RFM 5분위 규칙에서 파생되므로, 본 분류기는 그 규칙을 raw R/F/M 입력으로 **빠르게 재현하는 스코어러**다(전역 분위 재계산 없이 신규 고객 즉시 분류). 분위 동점 노이즈로 accuracy가 0.76 수준이며 단순 암기가 아니다.
