# app/services/datetime_parse.py
from __future__ import annotations

import re
from datetime import datetime, timedelta

FMT_DATE = "%Y-%m-%d"
FMT_DATETIME = "%Y-%m-%d %H:%M"


def parse_deadline(text: str) -> datetime | None:
    t = (text or "").strip().lower()
    if not t or t in {"-", "нет", "без дедлайна"}:
        return None

    # быстрые хэлперы
    now = datetime.now()
    if t in {"сегодня", "today"}:
        return now.replace(hour=23, minute=59, second=0, microsecond=0)
    if t in {"завтра", "tomorrow"}:
        d = now + timedelta(days=1)
        return d.replace(hour=18, minute=0, second=0, microsecond=0)

    # YYYY-MM-DD HH:MM
    m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})", t)
    if m:
        return datetime.strptime(t, FMT_DATETIME)

    # YYYY-MM-DD
    m = re.fullmatch(r"\d{4}-\d{2}-\d{2}", t)
    if m:
        d = datetime.strptime(t, FMT_DATE)
        return d.replace(hour=18, minute=0)

    raise ValueError(
        "Неверный формат даты. Используйте YYYY-MM-DD или YYYY-MM-DD HH:MM."
    )
