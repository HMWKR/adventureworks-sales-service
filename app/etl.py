# etl.py — 추출·변환·적재 (CRISP-DM 1~3단계: 데이터 이해·준비)
# ------------------------------------------------------------
# 노트북 AdventureSales_01_ETL / _02_Preprocessing 파이프라인을 재현한다.
#   1) MS Power BI AdventureWorks Sales.xlsx 다운로드(없으면)
#   2) 7개 시트 로드 → 키 기준 병합(denormalize)
#   3) 정제: 불필요 컬럼 제거, 타입 변환, 결측 정규화, 통합 Buyer 생성
#   4) 적재: SQLite(adventure_sales.db) + 전처리 CSV(processed_sales.csv)
# ------------------------------------------------------------
import socket
import sqlite3
import urllib.error
import urllib.request

import pandas as pd

from app import config


# ── 1. 다운로드 ──────────────────────────────────────────────
def download_excel(force: bool = False, timeout: int = 60) -> None:
    """원천 엑셀을 내려받는다(이미 있으면 생략).

    타임아웃·예외·파일 크기 검증을 포함하고, 실패 시 부분 파일을 정리한다.
    """
    if config.EXCEL_PATH.exists() and not force:
        return
    print(f"⬇️  다운로드: {config.EXCEL_URL}")
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    try:
        urllib.request.urlretrieve(config.EXCEL_URL, config.EXCEL_PATH)
        size = config.EXCEL_PATH.stat().st_size
        if size < 1024:  # 정상 파일은 수 MB
            config.EXCEL_PATH.unlink(missing_ok=True)
            raise RuntimeError(f"다운로드 파일이 비정상적으로 작음: {size} bytes")
        print(f"✅ 저장: {config.EXCEL_PATH} ({size:,} bytes)")
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        config.EXCEL_PATH.unlink(missing_ok=True)
        raise RuntimeError(f"엑셀 다운로드 실패: {e}") from e
    finally:
        socket.setdefaulttimeout(old_timeout)


# ── 2. 7개 시트 로드 + SQLite 원본 적재 ──────────────────────
def load_sheets() -> dict[str, pd.DataFrame]:
    """모든 시트를 사전 형태로 읽고, 필수 시트 존재를 검증한다."""
    if not config.EXCEL_PATH.exists():
        raise FileNotFoundError(f"엑셀 파일 없음: {config.EXCEL_PATH}")
    try:
        sheets = pd.read_excel(config.EXCEL_PATH, sheet_name=None)
    except ValueError as e:  # 손상 파일/파싱 오류
        raise RuntimeError(f"엑셀 파싱 실패: {e}") from e
    missing = set(config.SHEETS.values()) - set(sheets.keys())
    if missing:
        raise ValueError(f"필수 시트 누락: {missing} (보유: {list(sheets.keys())})")
    return sheets


def save_raw_sqlite(sheets: dict[str, pd.DataFrame]) -> None:
    """원천 7개 시트를 SQLite 테이블로 저장(노트북 01 재현)."""
    with sqlite3.connect(config.SQLITE_PATH) as conn:
        for sheet_name, df in sheets.items():
            table = sheet_name.replace(" ", "_")
            df.to_sql(table, conn, index=False, if_exists="replace")
    print(f"✅ SQLite 원본 적재: {config.SQLITE_PATH}")


# ── 3. 병합 + 정제 ───────────────────────────────────────────
def merge_sheets(sheets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """7개 시트를 키 기준으로 병합하여 denormalized fact 테이블 생성(노트북 02)."""
    s = config.SHEETS
    sales = sheets[s["sales"]]
    order = sheets[s["order"]]
    reseller = sheets[s["reseller"]]
    product = sheets[s["product"]]
    date = sheets[s["date"]]
    customer = sheets[s["customer"]]
    territory = sheets[s["territory"]]

    # 모든 병합에 명시적 suffixes 지정(중복 컬럼 충돌 시 원본 보존 + 명시적 접미사)
    m = sales.merge(order, on="SalesOrderLineKey", how="left", suffixes=("", "_order"))
    m = m.merge(reseller, on="ResellerKey", how="left", suffixes=("", "_reseller"))
    m = m.merge(product, on="ProductKey", how="left", suffixes=("", "_product"))
    m = m.merge(date, left_on="OrderDateKey", right_on="DateKey", how="left",
                suffixes=("", "_date"))
    m = m.merge(customer, on="CustomerKey", how="left", suffixes=("", "_cust"))
    m = m.merge(territory, on="SalesTerritoryKey", how="left", suffixes=("", "_terr"))
    return m


def preprocess(m: pd.DataFrame) -> pd.DataFrame:
    """정제: 결측 정규화, 날짜 변환, 통합 Buyer 생성, 핵심 컬럼 선택."""
    # 결측 표기 정규화
    m = m.replace(config.NA_TOKEN, pd.NA)

    # 날짜 타입
    m["Date"] = pd.to_datetime(m["Date"], errors="coerce")
    m["Year"] = m["Date"].dt.year
    m["Month"] = m["Date"].dt.month
    m["YearMonth"] = m["Date"].dt.to_period("M").astype(str)

    # 통합 Buyer: Internet 채널은 개인 고객, Reseller 채널은 리셀러를 구매자로
    is_internet = m["Channel"].eq("Internet")
    m["Buyer"] = m["Customer"].where(is_internet, m["Reseller"])
    m["Buyer Type"] = m["Channel"]

    # 핵심 컬럼만 선택(분석/모델링에 사용)
    keep = [
        "Date", "Year", "Month", "YearMonth",
        "Channel", "Buyer", "Buyer Type",
        "Business Type", "Group",
        "SKU", "Product", "Color", "Model", "Subcategory", "Category",
        "Standard Cost", "List Price", "Unit Price",
        "Product Standard Cost", "Total Product Cost",
        "Order Quantity", "Sales Amount", "Sales Order", "Sales Order Line",
        "City", "State-Province", "Country-Region", "Country", "Region", "Postal Code",
    ]
    cols = [c for c in keep if c in m.columns]
    df = m[cols].copy()

    # 수치형 안전 변환
    for col in ["Standard Cost", "List Price", "Unit Price",
                "Product Standard Cost", "Total Product Cost",
                "Order Quantity", "Sales Amount"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    n0 = len(df)
    # (1) 결측 제거 — 핵심 지표·그룹화 키(Buyer 포함, RFM groupby 무결성)
    df = df.dropna(subset=["Sales Amount", "Order Quantity", "Date", "Buyer"])
    n_missing = n0 - len(df)

    # (2) 중복 제거 — 완전 동일 행
    before = len(df)
    df = df.drop_duplicates()
    n_dup = before - len(df)

    # (3) 이상치 제거
    #   3a. 비정상 값: 매출/수량이 0 이하인 행
    before = len(df)
    df = df[(df["Sales Amount"] > 0) & (df["Order Quantity"] > 0)]
    n_nonpos = before - len(df)
    #   3b. 극단 이상치: 카테고리별 Sales Amount IQR 경계 밖
    #       (우편향 분포에서 전역 IQR은 고가 정상상품(자전거)을 오인 제거하므로
    #        카테고리별로 IQR을 적용해 스케일 차이를 보정한다)
    before = len(df)
    k = config.OUTLIER_IQR_MULT
    keep = pd.Series(True, index=df.index)
    for _, g in df.groupby("Category"):
        q1, q3 = g["Sales Amount"].quantile(0.25), g["Sales Amount"].quantile(0.75)
        iqr = q3 - q1
        lo, hi = q1 - k * iqr, q3 + k * iqr
        bad = g.index[(g["Sales Amount"] < lo) | (g["Sales Amount"] > hi)]
        keep.loc[bad] = False
    df = df[keep]
    n_outlier = before - len(df)

    df = df.reset_index(drop=True)
    print(f"   정제: 결측 {n_missing:,} · 중복 {n_dup:,} · 비정상 {n_nonpos:,} · "
          f"이상치 {n_outlier:,} 제거 → {len(df):,}행 (원본 {n0:,})")
    return df


# ── 4. 파이프라인 실행 ───────────────────────────────────────
def run_etl(force_download: bool = False, save_raw: bool = True) -> pd.DataFrame:
    """전체 ETL 실행 → 전처리 CSV 저장 + DataFrame 반환."""
    download_excel(force=force_download)
    sheets = load_sheets()
    if save_raw:
        save_raw_sqlite(sheets)
    merged = merge_sheets(sheets)
    df = preprocess(merged)

    # 전처리 결과 적재 (CSV + SQLite processed 테이블)
    df.to_csv(config.PROCESSED_CSV, index=False, encoding="utf-8-sig")
    with sqlite3.connect(config.SQLITE_PATH) as conn:
        df.to_sql("processed_sales", conn, index=False, if_exists="replace")

    print(f"✅ 전처리 완료: {df.shape[0]:,}행 × {df.shape[1]}열 → {config.PROCESSED_CSV.name}")
    return df


if __name__ == "__main__":
    run_etl()
