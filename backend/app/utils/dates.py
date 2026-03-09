from __future__ import annotations

from datetime import date, datetime, timezone


def ensure_utc(value: datetime | date | str | None) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return None
        if "T" in candidate:
            value = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
        else:
            value = date.fromisoformat(candidate)

    if isinstance(value, date) and not isinstance(value, datetime):
        value = datetime.combine(value, datetime.min.time(), tzinfo=timezone.utc)

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)
