# schemas.py — Pydantic 입출력 스키마 (View 계층, Swagger 자동 문서화)
# ------------------------------------------------------------
from pydantic import BaseModel, Field


# ── EDA 응답 ─────────────────────────────────────────────────
class MonthlySales(BaseModel):
    YearMonth: str
    sales_amount: float
    order_quantity: int
    order_lines: int


class RegionSales(BaseModel):
    Region: str | None = None
    sales_amount: float
    order_quantity: int
    order_lines: int


class CategorySales(BaseModel):
    Category: str | None = None
    sales_amount: float
    order_quantity: int
    order_lines: int


# ── RFM 응답 ─────────────────────────────────────────────────
class SegmentSummary(BaseModel):
    Segment: str
    customers: int
    avg_recency: float
    avg_frequency: float
    total_monetary: float


class CustomerRFM(BaseModel):
    buyer: str
    recency: int
    frequency: int
    monetary: float
    rfm_score: str
    segment: str


# ── 예측 요청/응답 ───────────────────────────────────────────
class SalesPredictRequest(BaseModel):
    order_quantity: int = Field(..., gt=0, le=1000, examples=[3])
    list_price: float = Field(..., ge=0, examples=[2000.0])
    standard_cost: float = Field(..., ge=0, examples=[1200.0])
    category: str = Field(..., examples=["Bikes"])
    subcategory: str = Field(..., examples=["Road Bikes"])
    channel: str = Field(..., examples=["Reseller"])
    region: str = Field(..., examples=["Southwest"])


class SalesPredictResponse(BaseModel):
    predicted_sales_amount: float


class SegmentPredictRequest(BaseModel):
    recency: int = Field(..., ge=0, examples=[30])
    frequency: int = Field(..., ge=0, examples=[5])
    monetary: float = Field(..., ge=0, examples=[15000.0])


class SegmentPredictResponse(BaseModel):
    segment: str
    confidence: float
    probabilities: dict[str, float]


class ForecastPoint(BaseModel):
    month: str
    forecast_sales_amount: float


class HistoryPoint(BaseModel):
    month: str
    sales_amount: float


class ForecastResponse(BaseModel):
    horizon: int
    history: list[HistoryPoint]
    forecast: list[ForecastPoint]
