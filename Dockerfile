# AdventureWorks 매출 분석·예측 서비스 — 컨테이너 이미지
# Hugging Face Spaces(Docker) / Render / Railway / 모든 컨테이너 호스트 호환.
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    MPLCONFIGDIR=/tmp/mpl \
    HF_HOME=/tmp/hf

# 의존성 먼저 설치(레이어 캐시)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 소스 복사
COPY . .

# 데이터 다운로드 + 4개 모델 학습을 이미지에 베이크 → 부팅 빠름
RUN python run_pipeline.py

# 런타임 쓰기 허용(예측 로그 로컬 폴백 등) + 비루트 환경 대비
RUN chmod -R 777 /app/data /app/models

EXPOSE 7860
# HF Spaces 는 7860, Render/Railway 는 $PORT 주입 → 둘 다 대응
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
