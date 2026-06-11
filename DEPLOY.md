# 🚀 배포 가이드 (Deployment)

이 앱은 FastAPI + Gradio + scikit-learn/statsmodels로 **무겁기 때문에**, Vercel 같은 서버리스가 아니라
**컨테이너 기반 호스트**(Hugging Face Spaces / Render / Railway)에 배포합니다. 저장소에 `Dockerfile`이 있어 어디서든 동일하게 빌드됩니다.

> 빌드 시 `run_pipeline.py`가 실행되어 데이터 다운로드 + 모델 4종 학습을 **이미지에 베이크**하므로, 배포 후 부팅이 빠릅니다(첫 빌드는 수 분 소요).
> 예측 로그는 환경변수 `SUPABASE_URL`/`SUPABASE_KEY`가 있으면 Supabase, 없으면 로컬에 저장됩니다(둘 다 동작).

---

## A. Hugging Face Spaces (무료, 추천) — Docker SDK

1. https://huggingface.co/new-space → **SDK: Docker**, 빈(Blank) 선택 → Space 생성
2. 생성된 Space의 README는 아래 **프론트매터로 시작**해야 합니다(이 한 가지만 HF 전용):
   ```
   ---
   title: AdventureWorks Sales Service
   emoji: 🚲
   colorFrom: blue
   colorTo: indigo
   sdk: docker
   app_port: 7860
   pinned: false
   ---
   ```
3. 이 저장소 파일 전체(특히 `Dockerfile`)를 Space 저장소에 push
   ```bash
   git remote add space https://huggingface.co/spaces/<USER>/<SPACE>
   git push space main
   ```
4. Space → **Settings → Variables and secrets** 에 시크릿 추가(선택, 예측 로그용):
   - `SUPABASE_URL` = `https://hthsvvwzrzbiowxazmdx.supabase.co`
   - `SUPABASE_KEY` = (Supabase publishable/anon key)
5. 빌드 완료(수 분) 후 `https://<USER>-<SPACE>.hf.space` 에서 라이브.

## B. Render (무료 플랜) — Docker

1. https://render.com → New → **Blueprint** → 이 저장소 선택 (루트 `render.yaml` 자동 인식)
   - 또는 New → Web Service → Docker 선택, `Dockerfile` 지정
2. Environment 에 `SUPABASE_URL` / `SUPABASE_KEY` 입력(선택)
3. Deploy → `https://adventureworks-sales-service.onrender.com` 에서 라이브
   - 무료 플랜은 비활성 시 슬립 → 첫 요청에 콜드스타트(수십 초) 발생

## C. 로컬 (발표 권장)

```bash
pip install -r requirements.txt
python run_pipeline.py        # 데이터+모델 준비(최초 1회)
uvicorn app.main:app --reload # http://127.0.0.1:8000
```
> 발표는 인터넷·콜드스타트 리스크가 없는 **로컬 실행이 가장 안전**합니다.

---

## 환경변수 (예측 로그)
| 변수 | 설명 |
|---|---|
| `SUPABASE_URL` | Supabase Project URL (예: `https://xxxx.supabase.co`) |
| `SUPABASE_KEY` | publishable(anon) key — RLS로 보호되는 클라이언트용 키 |

미설정 시 예측 로그는 컨테이너 내 로컬 SQLite(`data/predictions.db`)로 저장됩니다(영구 보존이 필요하면 Supabase 권장).
DB 테이블 준비: `adventureworks_predictions` (id, created_at, kind, inputs jsonb, output jsonb) + anon insert/select RLS 정책.
