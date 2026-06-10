# config.py — 경로/상수 중앙 관리
# ------------------------------------------------------------
# 데이터·모델 파일 경로와 도메인 상수를 한 곳에서 정의한다.
# ------------------------------------------------------------
from pathlib import Path

# 프로젝트 루트 (app/ 의 부모)
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MODEL_DIR = ROOT / "models"
DATA_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

# 원천 데이터 (Microsoft Power BI AdventureWorks Sales 샘플)
EXCEL_URL = (
    "https://github.com/microsoft/powerbi-desktop-samples/raw/main/"
    "AdventureWorks%20Sales%20Sample/AdventureWorks%20Sales.xlsx"
)
EXCEL_PATH = DATA_DIR / "AdventureWorks_Sales.xlsx"
SQLITE_PATH = DATA_DIR / "adventure_sales.db"
PROCESSED_CSV = DATA_DIR / "processed_sales.csv"   # 전처리 결과 (오프라인 실행용, 커밋 대상)

# 모델 산출물
REG_MODEL = MODEL_DIR / "sales_regressor.pkl"          # 매출 회귀 (RandomForestRegressor)
BUY_MODEL = MODEL_DIR / "buy_classifier.pkl"           # 구매 예측 Buy/Not (RandomForestClassifier)
CLF_MODEL = MODEL_DIR / "segment_classifier.pkl"       # 고객 RFM 세그먼트 분류 (보너스)
TS_MODEL = MODEL_DIR / "monthly_forecaster.pkl"        # 월 매출 시계열
METRICS_JSON = MODEL_DIR / "metrics.json"              # 학습 지표 (커밋 대상)

# 7개 원천 시트 이름
SHEETS = {
    "sales": "Sales_data",
    "order": "Sales Order_data",
    "reseller": "Reseller_data",
    "product": "Product_data",
    "date": "Date_data",
    "customer": "Customer_data",
    "territory": "Sales Territory_data",
}

# 결측 표기 정규화 대상
NA_TOKEN = "[Not Applicable]"

# 도메인 상수
FORECAST_HORIZON = 6        # 시계열 예측 기본 개월 수
SEASONAL_PERIODS = 12       # 연간 계절성
RANDOM_STATE = 42

# 회귀 입력 피처 (매출 예측)
REG_NUM_FEATURES = ["Order Quantity", "List Price", "Standard Cost"]
REG_CAT_FEATURES = ["Category", "Subcategory", "Channel", "Region"]
REG_TARGET = "Sales Amount"

# 구매 예측(Buy or Not) 입력 피처 — 고객×상품 카테고리 성향
# (CRM 관점: 어떤 고객이 어떤 물건을 구매하는지 예측)
BUY_NUM_FEATURES = ["prior_orders", "prior_monetary"]   # 고객의 과거 구매 횟수·금액
BUY_CAT_FEATURES = ["Region", "Channel", "Category"]    # 지역·채널 + 대상 상품 카테고리

# 이상치 제거 IQR 배수 (Sales Amount / Order Quantity)
OUTLIER_IQR_MULT = 3.0

# RFM 세그먼트 정의 (R/F/M 5분위 점수 기반)
RFM_SEGMENTS = [
    "Champions", "Loyal", "Potential Loyalist",
    "At Risk", "Hibernating", "Lost", "Others",
]
