# 📖 AdventureWorks 매출 분석·예측 서비스 — 사용 설명서

CRISP-DM 파이프라인으로 만든 매출 분석·예측 서비스의 상세 사용법입니다.
빠른 개요는 [README.md](README.md), 여기서는 화면·API·운영을 자세히 다룹니다.

---

## 1. 이 서비스는 무엇인가요?

Microsoft AdventureWorks(자전거 용품 도소매) 매출 데이터를 분석하고 미래를 예측하는 웹 서비스입니다.

- **데이터 분석(EDA)**: 월별·지역별·카테고리별 매출 현황
- **고객 분석(RFM)**: 우량/이탈 위험 고객 세그먼트
- **3가지 예측**: ① 주문 매출액(회귀) ② 고객 세그먼트(분류) ③ 미래 월매출(시계열)
- 화면(Gradio 대시보드) + 프로그램 연동용 API(Swagger) 동시 제공

---

## 2. 설치 및 실행

```bash
cd adventureworks_sales_service

# (권장) 가상환경
python -m venv .venv
.venv\Scripts\activate          # Windows

pip install -r requirements.txt

# 데이터 준비 + 모델 학습 (한 번만; 생략하면 첫 서버 기동 시 자동 실행)
python run_pipeline.py

# 서버 실행
uvicorn app.main:app --reload
```

- 대시보드: **http://127.0.0.1:8000/**
- API 문서: **http://127.0.0.1:8000/docs**

> 첫 실행은 원천 엑셀(약 14MB) 다운로드 + 12만 건 전처리 + 모델 3종 학습으로
> 수십 초~수 분 걸립니다. 콘솔에 `✅ 데이터·모델 준비 완료` 가 뜨면 됩니다.

---

## 3. 화면(대시보드) 사용법

### 3.1 📊 EDA 분석
- 상단 **KPI 카드**: 총매출·주문 수·판매 수량·구매자·제품·지역
- **월별 매출 추이** 라인차트, **지역별/카테고리별/채널별** 막대차트, 월별 집계표

### 3.2 👥 RFM 고객분석
- 세그먼트별 **고객 수·총 매출** 막대차트 + 요약표
- **Monetary 상위 우수 고객 20** 표
- 세그먼트: Champions(최우수) / Loyal / Potential Loyalist / At Risk / Hibernating / Lost / Others

### 3.3 💰 매출 예측 (회귀)
- 입력: 주문 수량, 정가, 표준원가, 카테고리, 서브카테고리, 채널, 지역
- `매출 예측하기` → 예측 매출액 카드 표시
- 학습에 없던 범주값을 넣으면 오류 메시지로 차단(신뢰할 수 없는 예측 방지)

### 3.4 🎯 고객 세그먼트 예측 (분류)
- 입력: Recency(마지막 구매 후 일수), Frequency(구매 횟수), Monetary(총 구매액)
- `세그먼트 예측하기` → 세그먼트 배지 + 확신도 + 확률 분포 차트

### 3.5 📈 시계열 예측
- 예측 개월 수(1~24) 슬라이더 → `예측 실행`
- 실제 vs 예측 월매출 라인차트 + 예측표

---

## 4. API 레퍼런스

`/docs`(Swagger)에서 바로 테스트할 수 있습니다.

### EDA `/api/eda`
| Method | URL | 설명 |
|---|---|---|
| GET | `/api/eda/summary` | 요약 통계 |
| GET | `/api/eda/monthly-sales` | 월별 매출 |
| GET | `/api/eda/region-sales` | 지역별 매출 |
| GET | `/api/eda/category-sales` | 카테고리별 매출 |
| GET | `/api/eda/channel-sales` | 채널별 매출 |
| GET | `/api/eda/top-products?n=10` | 상위 제품 |

### RFM `/api/rfm`
| Method | URL | 설명 |
|---|---|---|
| GET | `/api/rfm/segments` | 세그먼트 요약 |
| GET | `/api/rfm/top-customers?n=20` | 우수 고객 |
| GET | `/api/rfm/customer/{buyer}` | 특정 구매자 RFM |

### 예측 `/api/predict`
| Method | URL | 설명 |
|---|---|---|
| POST | `/api/predict/sales` | 매출 회귀 예측 |
| POST | `/api/predict/segment` | 고객 세그먼트 분류 |
| GET | `/api/predict/forecast?horizon=6` | 월매출 시계열 예측 |

### 요청 예시 (curl)
```bash
# 매출 예측
curl -X POST http://127.0.0.1:8000/api/predict/sales \
  -H "Content-Type: application/json" \
  -d "{\"order_quantity\":3,\"list_price\":2000,\"standard_cost\":1200,\"category\":\"Bikes\",\"subcategory\":\"Road Bikes\",\"channel\":\"Reseller\",\"region\":\"Southwest\"}"

# 세그먼트 분류
curl -X POST http://127.0.0.1:8000/api/predict/segment \
  -H "Content-Type: application/json" \
  -d "{\"recency\":30,\"frequency\":5,\"monetary\":15000}"

# 시계열 예측
curl "http://127.0.0.1:8000/api/predict/forecast?horizon=6"
```

---

## 5. 파이프라인 재실행 / 데이터 갱신

```bash
python run_pipeline.py            # ETL(있으면 재사용) + 모델 재학습
python run_pipeline.py --force    # 엑셀 강제 재다운로드부터
```

- 전처리 결과: `data/processed_sales.csv`, `data/adventure_sales.db`
- 모델: `models/*.pkl`, 지표: `models/metrics.json`

---

## 6. 비즈니스 규칙 / 모델 설계

| 항목 | 설명 |
|---|---|
| 통합 Buyer | Internet 채널=개인 고객, Reseller 채널=리셀러를 구매자로 통합 |
| 매출 회귀 피처 | 수량·정가·표준원가 + 카테고리·서브카테고리·채널·지역 (OneHot) |
| 세그먼트 분류 | R/F/M → RFM 규칙 세그먼트(빠른 스코어러), 입력은 raw R/F/M |
| 시계열 | Holt-Winters(가법 추세 damped + 가법 계절 12), 마지막 6개월 backtest |

정책 값은 `app/config.py`(`FORECAST_HORIZON`, `SEASONAL_PERIODS`, 피처 목록)에서 조정합니다.

---

## 7. FAQ

**Q. 첫 실행이 느려요.** → 14MB 다운로드 + 12만 건 전처리 + 모델 학습 때문입니다. 이후엔 캐시/저장 모델로 빠릅니다.

**Q. 포트 충돌.** → `uvicorn app.main:app --port 8011` 처럼 다른 포트 지정.

**Q. 처음부터 다시.** → `data/`·`models/` 파일 삭제 후 `python run_pipeline.py`.

**Q. 예측이 "알 수 없는 값" 오류.** → 학습 데이터에 없는 카테고리/지역 등을 입력한 경우입니다. 드롭다운의 값을 사용하세요.

**Q. 인터넷이 없는 환경.** → 최초 1회는 데이터 다운로드가 필요합니다. 이후 `data/`가 있으면 오프라인 동작합니다.
