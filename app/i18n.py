# i18n.py — 용어집(Glossary) 단일 출처(SSoT)
# ------------------------------------------------------------
# 영어 데이터 값(카테고리·채널·지역·세그먼트)의 한국어 뜻과 설명.
# 대시보드·플레이그라운드·Gradio·API 가 모두 이 정의를 공유한다.
# ------------------------------------------------------------

GLOSSARY: dict[str, dict[str, dict[str, str]]] = {
    # 상품 카테고리
    "category": {
        "Bikes":       {"ko": "자전거",   "desc": "완성 자전거(로드·산악·투어링) — 매출의 핵심 동력"},
        "Components":  {"ko": "부품",     "desc": "프레임·핸들·브레이크·기어 등 자전거 부품"},
        "Clothing":    {"ko": "의류",     "desc": "저지·반바지·양말·장갑 등 라이딩 의류"},
        "Accessories": {"ko": "액세서리", "desc": "헬멧·물통·펌프·청소용품 등 부속품"},
    },
    # 판매 채널
    "channel": {
        "Internet":  {"ko": "온라인(직접판매)", "desc": "개인 고객 대상 온라인 직접 판매 — B2C"},
        "Reseller":  {"ko": "리셀러(대리점)",   "desc": "대리점·소매점에 도매로 판매 — B2B"},
    },
    # 영업 지역
    "region": {
        "Northwest":      {"ko": "미국 북서부", "desc": "미국 북서부 영업 지역(북미)"},
        "Northeast":      {"ko": "미국 북동부", "desc": "미국 북동부 영업 지역(북미)"},
        "Central":        {"ko": "미국 중부",   "desc": "미국 중부 영업 지역(북미)"},
        "Southwest":      {"ko": "미국 남서부", "desc": "미국 남서부 — 매출 1위 지역(북미)"},
        "Southeast":      {"ko": "미국 남동부", "desc": "미국 남동부 영업 지역(북미)"},
        "Canada":         {"ko": "캐나다",     "desc": "캐나다 전역(북미)"},
        "France":         {"ko": "프랑스",     "desc": "프랑스(유럽)"},
        "Germany":        {"ko": "독일",       "desc": "독일(유럽)"},
        "United Kingdom": {"ko": "영국",       "desc": "영국(유럽)"},
        "Australia":      {"ko": "호주",       "desc": "호주(태평양)"},
    },
    # RFM 고객 세그먼트
    "segment": {
        "Champions":          {"ko": "충성 핵심고객",   "desc": "최근·자주·많이 구매하는 최우수 고객"},
        "Loyal":              {"ko": "단골고객",       "desc": "꾸준히 구매하는 충성 고객"},
        "Potential Loyalist": {"ko": "잠재 충성고객",   "desc": "최근 구매했고 단골이 될 가능성이 높음"},
        "At Risk":            {"ko": "이탈위험 고객",   "desc": "과거 우수했으나 최근 구매가 뜸해진 고객"},
        "Hibernating":        {"ko": "휴면고객",       "desc": "오랫동안 구매가 없는 고객"},
        "Lost":               {"ko": "이탈고객",       "desc": "최근성·빈도 모두 최저"},
        "Others":             {"ko": "기타",          "desc": "위 규칙에 속하지 않는 고객"},
    },
}

# 사람이 읽는 종류 이름
KIND_LABEL = {
    "category": "상품 카테고리",
    "channel": "판매 채널",
    "region": "영업 지역",
    "segment": "고객 세그먼트(RFM)",
}


def get_glossary() -> dict:
    """전체 용어집 반환(API·UI 주입용)."""
    return GLOSSARY


def label(kind: str, value: str, lang: str = "ko") -> str:
    """kind(category/channel/region/segment)의 value 를 lang 에 맞춰 라벨 변환."""
    if lang == "ko":
        item = GLOSSARY.get(kind, {}).get(value)
        if item:
            return item["ko"]
    return value
