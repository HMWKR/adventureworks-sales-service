#!/usr/bin/env python
# run_pipeline.py — ETL + 모델 학습을 한 번에 실행하는 편의 스크립트
# ------------------------------------------------------------
#   python run_pipeline.py           # ETL → 3개 모델 학습
#   python run_pipeline.py --force   # 엑셀 재다운로드부터
# ------------------------------------------------------------
import argparse

from app import etl, data_access
from app.ml import train
from app.services import rfm_service, ml_service


def main():
    ap = argparse.ArgumentParser(description="AdventureWorks ETL + 모델 학습")
    ap.add_argument("--force", action="store_true", help="엑셀 강제 재다운로드")
    args = ap.parse_args()

    print("1) ETL/전처리")
    etl.run_etl(force_download=args.force)
    data_access.reset_cache()
    rfm_service.reset_cache()

    print("2) 모델 학습")
    train.train_all()
    ml_service.reset_cache()

    print("\n✅ 파이프라인 완료. 서버 실행: uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()
