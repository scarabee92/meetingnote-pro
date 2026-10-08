"""받아쓴 기한 글자('다음 주 금요일' 등)를 날짜로 바꾼다. 못 바꾸면 None."""
import re
from datetime import date, timedelta

WEEKDAY = {"월": 0, "화": 1, "수": 2, "목": 3, "금": 4, "토": 5, "일": 6}


def parse_due(text: str | None, base: date) -> date | None:
    if not text:
        return None
    t = re.sub(r"\s+", "", text.strip())
    if not t or t in ("미정", "없음", "-"):
        return None
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", t)
    if m:
        try:
            return date(int(m[1]), int(m[2]), int(m[3]))
        except ValueError:
            return None
    if t in ("오늘", "금일"):
        return base
    if t == "내일":
        return base + timedelta(days=1)
    if t == "모레":
        return base + timedelta(days=2)
    m = re.fullmatch(r"(이번|다음)주?(?:주)?([월화수목금토일])(?:요일)?", t)
    if m:
        monday = base - timedelta(days=base.weekday())
        week = monday + timedelta(days=7 if m[1] == "다음" else 0)
        return week + timedelta(days=WEEKDAY[m[2]])
    m = re.fullmatch(r"(\d{1,2})월(\d{1,2})일?", t)
    if m:
        try:
            d = date(base.year, int(m[1]), int(m[2]))
        except ValueError:
            return None
        if (base - d).days > 180:  # 한참 앞서면 내년으로
            d = date(base.year + 1, int(m[1]), int(m[2]))
        return d
    return None
