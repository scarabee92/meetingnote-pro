from datetime import date, datetime, timezone


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def norm_iso(value: str) -> str | None:
    """ISO 8601 문자열을 UTC 'YYYY-MM-DDTHH:MM:SSZ' 로. 해석하지 못하면 None."""
    try:
        v = value.strip().replace("Z", "+00:00")
        d = datetime.fromisoformat(v)
    except (ValueError, AttributeError):
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_date(value: str | None) -> str | None:
    """'YYYY-MM-DD' 만 받는다. 아니면 None."""
    if not value:
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        return None
