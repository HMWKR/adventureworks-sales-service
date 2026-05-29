# 🚲 AdventureWorks 매출 분석·예측 서비스

> **이 문서 하나만 읽으면** 이 프로젝트가 무엇이고, 어떻게 만들어졌고, 어떻게 실행하고, 어떻게 쓰는지 전부 알 수 있습니다.

Microsoft **AdventureWorks(자전거 용품 도소매)** 매출 데이터를 **수집 → 분석 → 머신러닝 예측 → 웹 서비스**로 연결한 풀 파이프라인 프로젝트입니다. 데이터 분석을 몰라도 화면을 따라가면 *"무엇이 팔리고, 누가 사고, 앞으로 어떻게 될지"* 를 1분 안에 이해할 수 있게 설계했습니다.

`week13 FastAPI-MVC.pptx` 기말과제(CRISP-DM 적용)를 실제 동작하는 서비스로 구현했습니다.

---

## 📑 목차
1. [한눈에 보기](#1-한눈에-보기)
2. [5분 만에 실행하기](#2-5분-만에-실행하기)
3. [무엇을 볼 수 있나요 — 3개 화면과 사용자 흐름](#3-무엇을-볼-수-있나요--3개-화면과-사용자-흐름)
4. [어떻게 만들었나요 — CRISP-DM 제작 과정](#4-어떻게-만들었나요--crisp-dm-제작-과정)
5. [데이터 파이프라인](#5-데이터-파이프라인)
6. [분석 & 머신러닝](#6-분석--머신러닝)
7. [API 레퍼런스](#7-api-레퍼런스)
8. [프로젝트 구조](#8-프로젝트-구조)
9. [디자인 시스템 (Toss 스타일)](#9-디자인-시스템-toss-스타일)
10. [테스트](#10-테스트)
11. [자주 묻는 질문 / 트러블슈팅](#11-자주-묻는-질문--트러블슈팅)

---

## 1. 한눈에 보기

| 항목 | 내용 |
|---|---|
| **무엇** | 매출 데이터 분석 대시보드 + 3가지 머신러닝 예측(매출·고객·미래) 웹 서비스 |
| **데이터** | MS Power BI `AdventureWorks Sales.xlsx` (7시트) → 정제 **121,253행 / 36개월** |
| **분석** | EDA(월·지역·카테고리·채널) + RFM 고객 세그먼트(7종) + 자동 인사이트(5종) |
| **예측** | ① 매출 회귀(R² 0.98) ② 고객 세그먼트 분류(정확도 0.76) ③ 월매출 시계열(backtest MAPE 21.5%) |
| **화면** | 스토리 대시보드(`/`) · 예측 플레이그라운드(`/playground`) · Gradio(`/gradio`) · Swagger(`/docs`) |
| **기술** | FastAPI · pandas · scikit-learn · statsmodels · Jinja2 · ECharts · Gradio |
| **설계** | MVC 레이어드 아키텍처 + Toss 스타일 디자인 시스템 |

---

## 2. 5분 만에 실행하기

```bash
cd adventureworks_sales_service

# 1) (권장) 가상환경
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# 2) 의존성 설치 (11개)
pip install -r requirements.txt

# 3) (선택) 데이터 준비 + 모델 학습을 미리 실행
#    생략해도 첫 서버 기동 시 자동으로 수행됩니다.
python run_pipeline.py

# 4) 서버 실행
uvicorn app.main:app --reload
```

브라우저에서 접속하세요:

| 주소 | 화면 |
|---|---|
| **http://127.0.0.1:8000/** | 📖 스토리 대시보드 (여기서 시작) |
| http://127.0.0.1:8000/playground | 🔮 예측 플레이그라운드 |
| http://127.0.0.1:8000/gradio | 🎛️ Gradio 버전 |
| http://127.0.0.1:8000/docs | 📑 Swagger API 문서 |

> ⏱️ **첫 실행은 시간이 걸립니다.** 서버가 처음 켜질 때 원천 엑셀(약 14MB)을 자동 다운로드하고, 12만 행을 전처리하고, 모델 3개를 학습합니다(네트워크·디스크 속도에 따라 수십 초~수 분). 콘솔에 `✅ 데이터·모델 준비 완료` 가 뜨면 됩니다. 미리 `python run_pipeline.py` 로 준비해 두면 서버 기동이 빨라집니다.

---

## 3. 무엇을 볼 수 있나요 — 3개 화면과 사용자 흐름

이 서비스는 **하나의 이야기**처럼 설계됐습니다. 처음 방문하면 이렇게 흘러갑니다.

```
[ / 스토리 대시보드 ]  →  "데이터가 말해주는 사실을 읽는다"
   요약(한눈에) → 무엇이 팔리나 → 누가 사나 → 앞으로는?
        │
        │  "직접 예측해보고 싶다"  (CTA 버튼: 예측 해보기 →)
        ▼
[ /playground 예측 플레이그라운드 ]  →  "내 조건으로 직접 예측한다"
   매출 예측 · 고객 세그먼트 · 시계열 예측 (탭으로 전환)
        │
        │  "원본 API/강의용 버전이 궁금하다"
        ▼
[ /docs Swagger ]   /   [ /gradio Gradio 버전 ]
```

### 3-1. 📖 스토리 대시보드 (`/`) — 시작점
스크롤하며 데이터의 이야기를 따라가는 화면입니다. 4개 섹션으로 구성됩니다.

| 섹션 | 내용 |
|---|---|
| **요약 (Overview)** | KPI 5개(총매출·주문수·구매자·제품·평균주문액) + **자동 생성 인사이트 카드 5개** |
| **무엇이 팔리나 (What)** | 월별 매출 추이(라인) · 카테고리 구성(도넛) · 지역별 TOP(가로 막대) · 베스트셀러 제품(가로 막대) |
| **누가 사나 (Who)** | 세그먼트별 고객 수 · 세그먼트별 매출 기여 (RFM 분석) |
| **앞으로는 (Future)** | 실제 vs 예측 월매출(실선=실제, 점선=예측) + 예측하러 가기 CTA |

- **자동 인사이트**란? 데이터가 스스로 찾아낸 한 문장 사실입니다. 예: *"최근 12개월 매출이 직전 12개월 대비 +52.3% 성장했어요"*, *"'Bikes'가 전체 매출의 86%를 차지하는 핵심 동력이에요"*, *"'Champions' 2,444명이 전체 매출의 69%를 책임지는 우량 고객이에요"*.
- 차트는 **ECharts**로 그리며, 스크롤해서 화면에 들어올 때 하나씩 로드(lazy-init)되어 가볍습니다.

### 3-2. 🔮 예측 플레이그라운드 (`/playground`) — 직접 해보기
상단 **세그먼트 컨트롤(탭)**로 3가지 도구를 전환합니다. 입력하면 학습된 모델이 즉시 결과를 알려줍니다.

| 도구 | 입력 | 결과 |
|---|---|---|
| **💰 매출 예측** | 주문수량·정가·표준원가 + 카테고리·서브카테고리·채널·지역 | 예측 매출액 (예: `$3,846.66`) |
| **🎯 고객 세그먼트** | Recency·Frequency·Monetary | 세그먼트 배지 + 확신도 + 세그먼트별 확률 막대 |
| **📈 시계열 예측** | 예측 개월 수(1~24 슬라이더) | 실제+예측 월매출 차트 |

> 입력 폼은 `/api/predict/*` 를 호출하고, 결과는 카드/차트로 렌더합니다. 드롭다운 선택지(카테고리·지역 등)는 실제 데이터에서 자동으로 채워집니다.

### 3-3. 🎛️ Gradio 버전 (`/gradio`) — 강의용 데모
강의 커리큘럼의 `gr.mount_gradio_app` 패턴을 보존한 버전입니다. 5개 탭(EDA·RFM·매출 예측·세그먼트 예측·시계열 예측)으로 동일 기능을 제공하며, 동일한 Toss 라이트 테마로 꾸몄습니다.

---

## 4. 어떻게 만들었나요 — CRISP-DM 제작 과정

데이터마이닝 표준 방법론 **CRISP-DM** 5단계를 그대로 따라 만들었습니다.

| 단계 | 한 일 | 구현 위치 |
|---|---|---|
| **1. 비즈니스·데이터 이해** | AdventureWorks 매출 구조 파악, 7개 시트 분석 | `app/etl.py`, `app/services/eda_service.py` |
| **2. 데이터 준비** | 7시트 다운로드·병합·정제, 통합 Buyer 생성 → SQLite/CSV | `app/etl.py`, `app/data_access.py` |
| **3. 모델링** | 회귀·분류·시계열 3개 모델 학습 | `app/ml/train.py` |
| **4. 평가** | R²/MAE/정확도/F1/MAPE + 시계열 backtest | `models/metrics.json` |
| **5. 배포** | FastAPI 서비스 + 대시보드/플레이그라운드/Gradio + 테스트 | `app/main.py`, `app/web/`, `tests/` |

---

## 5. 데이터 파이프라인

### 원천 데이터
- **출처**: Microsoft Power BI 공식 샘플 — `https://github.com/microsoft/powerbi-desktop-samples/.../AdventureWorks Sales.xlsx`
- **7개 시트**: `Sales_data`, `Sales Order_data`, `Reseller_data`, `Product_data`, `Date_data`, `Customer_data`, `Sales Territory_data`

### 처리 흐름 (`app/etl.py`)
```
다운로드 → 7시트 로드 → 키 기준 병합(left join) → 정제 → SQLite + CSV 적재
```
- **병합 키**: SalesOrderLineKey · ResellerKey · ProductKey · OrderDateKey→DateKey · CustomerKey · SalesTerritoryKey
- **정제**:
  - `[Not Applicable]` → 결측(`pd.NA`) 정규화
  - `Date` → datetime 변환 + `Year`/`Month`/`YearMonth` 파생
  - **통합 Buyer**: Internet 채널이면 Customer를, Reseller 채널이면 Reseller를 구매자로 통합 (RFM 분석을 위해)
  - 핵심 27개 컬럼 선택, `Sales Amount`·`Order Quantity`·`Date`·`Buyer` 결측 행 제거
- **산출물**: `data/adventure_sales.db`(SQLite, 원본 7시트 + `processed_sales` 테이블), `data/processed_sales.csv`(UTF-8-sig)
- **결과**: **121,253행 / 36개월**
- **캐시**: `@lru_cache(maxsize=1)` 로 1회만 메모리 로드. CSV가 없으면 ETL 자동 실행.

---

## 6. 분석 & 머신러닝

### 6-1. EDA (집계 4종)
월별 · 지역별 · 카테고리별 · 채널별(Internet/Reseller) 매출 집계. 각각 `sales_amount`, `order_quantity`, `order_lines`.

### 6-2. RFM 고객 세그먼트
구매자(Buyer)별 **R**ecency(최근성)·**F**requency(빈도)·**M**onetary(금액)를 5분위 점수(1~5)로 매기고, 규칙으로 7개 세그먼트를 부여합니다.

| 세그먼트 | 규칙 |
|---|---|
| **Champions** | R≥4 & F≥4 & M≥4 |
| **Loyal** | R≥3 & F≥3 |
| **Potential Loyalist** | R≥4 & F≤2 |
| **At Risk** | R≤2 & F≥3 |
| **Hibernating** | R≤2 & F≤2 & M≥3 |
| **Lost** | R≤1 & F≤1 |
| **Others** | 그 외 |

### 6-3. 머신러닝 모델 3종 (`app/ml/train.py` → `models/*.pkl`)

| 모델 | 알고리즘 | 입력 → 출력 | 성능 |
|---|---|---|---|
| **매출 회귀** | `RandomForestRegressor`(n=80, depth=18) | 수량·정가·원가 + 카테고리·서브카테고리·채널·지역(OneHot) → 매출액 | **R²=0.9811**, MAE=21.83, RMSE=234.28 (train 97,002 / test 24,251) |
| **고객 분류** | `RandomForestClassifier`(n=100, depth=12, balanced) | R·F·M → 7개 세그먼트 | **정확도=0.7623**, macro-F1=0.7439 (train 15,226 / test 3,807) |
| **월매출 시계열** | Holt-Winters(가법추세 damped + 가법계절 12) | 36개월 → 향후 N개월 | in-MAPE 27.52%, **backtest-MAPE 21.5%** (마지막 6개월 holdout) |

> **분류 모델 클래스별 F1**: Champions 0.998(최고) … Lost 0.483(최저). 세그먼트 라벨은 RFM 5분위 규칙에서 파생되므로, 이 분류기는 그 규칙을 raw R/F/M로 빠르게 재현하는 **스코어러**입니다(전역 분위 재계산 없이 신규 고객 즉시 분류).
>
> **회귀 입력 검증**: 학습에 없던 카테고리/지역 등을 넣으면 `InvalidInput` 예외(400)로 차단해, 신뢰할 수 없는 예측을 방지합니다.

### 6-4. 자동 인사이트 5종 (`app/services/insight_service.py`)
① 연간 성장(최근 12개월 vs 직전 12개월) ② 카테고리 1위 비중 ③ 지역 1위 비중 ④ 핵심 고객층(세그먼트 1위) ⑤ 미래 전망(향후 6개월 vs 최근 6개월).

---

## 7. API 레퍼런스

모든 API는 `/docs`(Swagger)에서 바로 테스트할 수 있습니다. 라우터는 `/api` 프리픽스로 통합됩니다.

### EDA — `/api/eda`
| Method | 경로 | 응답 |
|---|---|---|
| GET | `/api/eda/summary` | 전체 요약 통계 |
| GET | `/api/eda/monthly-sales` | `[{YearMonth, sales_amount, order_quantity, order_lines}]` |
| GET | `/api/eda/region-sales` | 지역별 매출 (내림차순) |
| GET | `/api/eda/category-sales` | 카테고리별 매출 |
| GET | `/api/eda/channel-sales` | 채널별 매출 |
| GET | `/api/eda/top-products?n=10` | 매출 상위 제품 |

### RFM — `/api/rfm`
| Method | 경로 | 응답 / 비고 |
|---|---|---|
| GET | `/api/rfm/segments` | `[{Segment, customers, avg_recency, avg_frequency, total_monetary}]` |
| GET | `/api/rfm/top-customers?n=20` | Monetary 상위 고객 |
| GET | `/api/rfm/customer/{buyer}` | 개별 고객 RFM (없으면 **404**) |

### 예측 — `/api/predict`
| Method | 경로 | 요청 → 응답 |
|---|---|---|
| POST | `/api/predict/sales` | `{order_quantity(1~1000), list_price, standard_cost, category, subcategory, channel, region}` → `{predicted_sales_amount}` · 미지 범주 시 **400**, 검증 실패 시 **422** |
| POST | `/api/predict/segment` | `{recency, frequency, monetary}` → `{segment, confidence, probabilities}` |
| GET | `/api/predict/forecast?horizon=6` | (1~24) → `{horizon, history:[{month, sales_amount}], forecast:[{month, forecast_sales_amount}]}` |

### 인사이트·메타
| Method | 경로 | 응답 |
|---|---|---|
| GET | `/api/insights` | 자동 인사이트 배열 `[{icon, title, metric, text}]` |
| GET | `/api/insights/dashboard` | 대시보드 전체 데이터 번들(차트+인사이트) |
| GET | `/api` | API 인덱스(섹션별 엔드포인트 목록) |
| GET | `/health` | `{status: "ok"}` |

#### 요청 예시
```bash
curl -X POST http://127.0.0.1:8000/api/predict/sales \
  -H "Content-Type: application/json" \
  -d "{\"order_quantity\":3,\"list_price\":2000,\"standard_cost\":1200,\"category\":\"Bikes\",\"subcategory\":\"Road Bikes\",\"channel\":\"Reseller\",\"region\":\"Southwest\"}"

curl -X POST http://127.0.0.1:8000/api/predict/segment \
  -H "Content-Type: application/json" -d "{\"recency\":30,\"frequency\":5,\"monetary\":15000}"

curl "http://127.0.0.1:8000/api/predict/forecast?horizon=6"
```

---

## 8. 프로젝트 구조

```
adventureworks_sales_service/
├── app/
│   ├── config.py            # 경로·상수 (데이터/모델 경로, 피처, 시드)
│   ├── etl.py               # 추출·변환·적재 (다운로드→병합→정제→SQLite/CSV)
│   ├── data_access.py       # 전처리 데이터 캐시 로더
│   ├── schemas.py           # Pydantic 입출력 스키마 (View)
│   ├── services/            # 비즈니스 로직 (Model)
│   │   ├── eda_service.py   #   집계
│   │   ├── rfm_service.py   #   RFM 분석·세그먼트
│   │   ├── ml_service.py    #   모델 로드·추론 (지연로딩 캐시)
│   │   └── insight_service.py  # 자동 인사이트 + 대시보드 페이로드
│   ├── ml/train.py          # 모델 학습 파이프라인 (3종 → models/*.pkl)
│   ├── routers/             # API 엔드포인트 (Controller)
│   │   ├── eda.py / rfm.py / predict.py / insights.py
│   ├── web/router.py        # 스토리 대시보드(/) + 플레이그라운드(/playground)
│   ├── templates/           # Jinja2: dashboard.html / playground.html
│   ├── static/css/toss.css  # Toss 디자인 시스템
│   ├── static/js/           # dashboard.js / playground.js (ECharts)
│   ├── ui/gradio_app.py     # Gradio 버전 (Toss 테마, /gradio)
│   └── main.py              # 앱 조립 + 라우터/정적/ Gradio mount + lifespan
├── tests/test_api.py        # pytest 21 케이스
├── run_pipeline.py          # ETL + 모델 학습 일괄 실행
├── models/metrics.json      # 학습 지표(커밋됨)
├── requirements.txt
├── README.md (이 문서) · USER_GUIDE.md (상세 사용법)
```

**MVC 매핑** — Model: `services/*` + `ml/train.py` + `etl.py` · View: `schemas.py` + `templates/` + `static/` · Controller: `routers/*` + `web/router.py` + `main.py`

> ⚙️ **자동 워밍업**: `main.py`의 `lifespan`이 서버 시작 시 데이터·모델을 1회 준비합니다(없으면 ETL·학습 자동 트리거). 그래서 별도 준비 없이 `uvicorn`만으로도 동작합니다.

---

## 9. 디자인 시스템 (Toss 스타일)

세 화면이 **하나의 디자인 언어**를 공유합니다 (`app/static/css/toss.css`).

| 토큰 | 값 |
|---|---|
| **컬러** | primary `#3182f6` · hover `#1b64da` · 본문 `#191f28` · 보조 `#4e5968` · 배경 `#f9fafb` · 긍정 `#1bbf83` |
| **타이포** | Pretendard / Segoe UI · 히어로 2.6rem · KPI 2rem |
| **모서리** | 카드 18px · 버튼 14px · 입력 12px |
| **그림자** | `0 1px 2px / 0 4px 16px rgba(0,0,0,.04)` (soft) |

특징: 넉넉한 여백, 카드 기반 레이아웃, 친근한 마이크로카피, 스크롤 등장 애니메이션, 모바일 반응형(640px/860px), Gradio도 CSS 변수 오버라이드로 동일 라이트 테마 적용.

---

## 10. 테스트

```bash
pytest -q            # 21개 케이스
```
**커버리지**: 메타/화면(6) · EDA(4) · RFM(3) · 매출 예측(3, 422/400 검증 포함) · 세그먼트(2) · 시계열(2). `TestClient` 진입 시 lifespan으로 데이터·모델이 자동 워밍업됩니다.

---

## 11. 자주 묻는 질문 / 트러블슈팅

**Q. 첫 실행이 느려요.** → 14MB 다운로드 + 12만 행 전처리 + 모델 3개 학습 때문입니다. `python run_pipeline.py` 로 미리 준비하면 빨라집니다.

**Q. 포트를 바꾸고 싶어요.** → `uvicorn app.main:app --reload --port 8011`

**Q. 처음부터 다시 만들고 싶어요.** → `data/`·`models/` 의 생성물 삭제 후 `python run_pipeline.py` (또는 `--force` 로 엑셀 재다운로드).

**Q. "알 수 없는 값" 예측 오류가 나요.** → 학습 데이터에 없는 카테고리/지역을 입력한 경우입니다. 화면 드롭다운의 값을 사용하세요.

**Q. 오프라인에서도 되나요?** → `data/`·`models/` 파일이 있으면 됩니다. 최초 1회는 엑셀 다운로드를 위해 인터넷이 필요합니다.

**Q. 데이터/모델 파일이 저장소에 없어요.** → 용량 때문에 `.gitignore` 처리되어 ETL/학습으로 재생성됩니다(`models/metrics.json`만 커밋). 위 실행 절차대로 하면 자동 생성됩니다.

---

### 기술 스택
FastAPI · Uvicorn · pandas · NumPy · scikit-learn · statsmodels · openpyxl · Pydantic · Jinja2 · ECharts 5.5 · Gradio · pytest

### 데이터 출처
Microsoft Power BI Desktop Samples — AdventureWorks Sales (공개 샘플)

_FastAPI + Gradio + ECharts · AdventureWorks Sales · 기말과제 (CRISP-DM)_
