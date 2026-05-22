from __future__ import annotations

import datetime as dt
from collections import Counter, defaultdict

from agent.storage.db import AgentDB


def compute_daily_habits(db: AgentDB, *, user_id: str, day: dt.date) -> dict:
    """
    Returns a small set of useful daily stats.
    """
    start = dt.datetime.combine(day, dt.time.min).timestamp()
    end = dt.datetime.combine(day, dt.time.max).timestamp()

    with db.connect() as con:
        rows = con.execute(
            """
            SELECT ts, user_text
            FROM events
            WHERE user_id=? AND ts BETWEEN ? AND ?
            ORDER BY ts ASC
            """,
            (user_id, float(start), float(end)),
        ).fetchall()

    hours = Counter()
    commands = Counter()
    total_messages = 0

    for r in rows:
        total_messages += 1
        ts = float(r["ts"])
        text = str(r["user_text"] or "").strip()
        try:
            hour = dt.datetime.fromtimestamp(ts).hour
            hours[str(hour).zfill(2)] += 1
        except Exception:
            pass

        if text.startswith("/"):
            cmd = text[1:].split(maxsplit=1)[0]
            if cmd:
                commands[cmd] += 1

    top_hours = [h for h, _ in hours.most_common(5)]
    top_cmds = [c for c, _ in commands.most_common(10)]
    return {
        "day": day.isoformat(),
        "user_id": user_id,
        "total_messages": total_messages,
        "top_hours": top_hours,
        "top_commands": top_cmds,
    }


def compute_week_profile(db: AgentDB, *, user_id: str, end_day: dt.date | None = None, days: int = 7) -> dict:
    end_day = end_day or dt.date.today()
    start_day = end_day - dt.timedelta(days=days - 1)

    day_counts: dict[str, int] = {}
    hour_counts: Counter[str] = Counter()
    cmd_counts: Counter[str] = Counter()

    with db.connect() as con:
        rows = con.execute(
            """
            SELECT ts, user_text
            FROM events
            WHERE user_id=? AND ts BETWEEN ? AND ?
            ORDER BY ts ASC
            """,
            (
                user_id,
                dt.datetime.combine(start_day, dt.time.min).timestamp(),
                dt.datetime.combine(end_day, dt.time.max).timestamp(),
            ),
        ).fetchall()

    for r in rows:
        ts = float(r["ts"])
        text = str(r["user_text"] or "").strip()
        d = dt.datetime.fromtimestamp(ts).date().isoformat()
        day_counts[d] = day_counts.get(d, 0) + 1

        hour_counts[str(dt.datetime.fromtimestamp(ts).hour).zfill(2)] += 1
        if text.startswith("/"):
            cmd = text[1:].split(maxsplit=1)[0]
            if cmd:
                cmd_counts[cmd] += 1

    return {
        "from_day": start_day.isoformat(),
        "to_day": end_day.isoformat(),
        "user_id": user_id,
        "messages_per_day": day_counts,
        "top_hours": [h for h, _ in hour_counts.most_common(8)],
        "top_commands": [c for c, _ in cmd_counts.most_common(12)],
    }

