# log_service.py — 예측 로그 저장/조회 (Supabase 우선, 로컬 SQLite 폴백)
# ------------------------------------------------------------
# 사용자가 돌린 예측을 기록한다.
#   - SUPABASE_URL / SUPABASE_KEY 환경변수가 설정되면 → Supabase(Postgres)에 저장
#   - 없거나 실패하면 → 로컬 SQLite(data/predictions.db)로 폴백
# 어느 경우든 예측 자체는 절대 막지 않는다(로그 실패는 조용히 무시).
# ------------------------------------------------------------
import os
import json
import sqlite3
import datetime as dt

import httpx

from app import config

TABLE = "adventureworks_predictions"
_LOCAL_DB = config.DATA_DIR / "predictions.db"


def _supabase():
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_KEY", "")
    return (url, key) if (url and key) else (None, None)


def source() -> str:
    """현재 로그 저장소('supabase' 또는 'local')."""
    return "supabase" if _supabase()[0] else "local"


def _headers(key: str) -> dict:
    return {"apikey": key, "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"}


def _local_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_LOCAL_DB)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS predictions ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT, kind TEXT,"
        "inputs TEXT, output TEXT)"
    )
    return conn


def log_prediction(kind: str, inputs: dict, output: dict) -> dict:
    """예측 1건 기록. 반환: {'stored': 'supabase'|'local'|'none'}."""
    url, key = _supabase()
    if url:
        try:
            r = httpx.post(
                f"{url}/rest/v1/{TABLE}",
                headers={**_headers(key), "Prefer": "return=minimal"},
                json={"kind": kind, "inputs": inputs, "output": output},
                timeout=5.0,
            )
            if r.status_code in (200, 201, 204):
                return {"stored": "supabase"}
        except Exception:
            pass  # → 로컬 폴백
    try:
        with _local_conn() as c:
            c.execute(
                "INSERT INTO predictions (created_at, kind, inputs, output) VALUES (?,?,?,?)",
                (dt.datetime.now().isoformat(timespec="seconds"), kind,
                 json.dumps(inputs, ensure_ascii=False), json.dumps(output, ensure_ascii=False)),
            )
        return {"stored": "local"}
    except Exception:
        return {"stored": "none"}


def recent_predictions(limit: int = 10) -> list[dict]:
    """최근 예측 기록 조회(최신순)."""
    limit = max(1, min(int(limit), 100))
    url, key = _supabase()
    if url:
        try:
            r = httpx.get(
                f"{url}/rest/v1/{TABLE}",
                params={"select": "created_at,kind,inputs,output",
                        "order": "created_at.desc", "limit": limit},
                headers=_headers(key), timeout=5.0,
            )
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
    try:
        with _local_conn() as c:
            c.row_factory = sqlite3.Row
            rows = c.execute(
                "SELECT created_at, kind, inputs, output FROM predictions "
                "ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [{"created_at": r["created_at"], "kind": r["kind"],
                 "inputs": json.loads(r["inputs"]), "output": json.loads(r["output"])}
                for r in rows]
    except Exception:
        return []
