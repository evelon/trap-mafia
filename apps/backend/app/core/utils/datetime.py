from datetime import datetime, timezone

from app.schemas.common.datetime import UtcDatetime


def now_utc_iso() -> UtcDatetime:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
