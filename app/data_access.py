# data_access.py — 전처리 데이터 로딩(캐시)
# ------------------------------------------------------------
# 서비스 계층이 공유하는 단일 진입점. processed_sales.csv 를 메모리에 한 번만
# 로드하여 캐시한다. 파일이 없으면 ETL 을 자동 실행한다.
# ------------------------------------------------------------
from functools import lru_cache

import pandas as pd

from app import config


@lru_cache(maxsize=1)
def get_dataframe() -> pd.DataFrame:
    """전처리된 매출 데이터프레임을 반환(최초 1회 로드 후 캐시)."""
    if not config.PROCESSED_CSV.exists():
        # 전처리 결과가 없으면 ETL 실행
        from app import etl
        return etl.run_etl()
    df = pd.read_csv(config.PROCESSED_CSV, low_memory=False)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    return df


def reset_cache() -> None:
    """캐시 무효화(데이터 갱신 후 호출)."""
    get_dataframe.cache_clear()
