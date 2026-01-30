from datetime import datetime, timezone as dt_timezone

class timezone:
    datetime = datetime

    @staticmethod
    def now():
        return datetime.now(dt_timezone.utc)

def parse_datetime(date_string: str) -> datetime:
    # ISO 8601 parser fallback
    return datetime.fromisoformat(date_string.replace("Z", "+00:00"))