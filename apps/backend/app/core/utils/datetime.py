from datetime import datetime, timezone

from app.schemas.common.datetime import UtcDatetime


def now_utc_iso() -> UtcDatetime:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def datetime_to_utc_iso(time: datetime) -> UtcDatetime:
    if time.tzinfo is None:
        time = time.replace(tzinfo=timezone.utc)

    iso = time.isoformat(timespec="milliseconds")
    if iso.endswith("Z"):
        iso = iso[:-1]
    elif iso.endswith("+00:00"):
        iso = iso[:-6]
    return iso + "Z"
