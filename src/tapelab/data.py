"""CSV loading and validation for standard OHLCV data."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

from tapelab.models import Bar

REQUIRED_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume")


def _parse_timestamp(value: str) -> datetime:
    text = value.strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid ISO 8601 timestamp {value!r}") from exc
    # Date-only or timezone-naive timestamps are interpreted as UTC by convention.
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_bars(path: str | Path) -> tuple[Bar, ...]:
    """Load ascending, unique OHLCV bars from a UTF-8 CSV file.

    Required columns are ``timestamp,open,high,low,close,volume``. Extra
    columns are ignored. Naive timestamps are interpreted as UTC.
    """

    source = Path(path)
    try:
        stream = source.open("r", encoding="utf-8-sig", newline="")
    except OSError as exc:
        raise ValueError(f"cannot read data file {source}: {exc}") from exc

    with stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None:
            raise ValueError("CSV is empty or has no header row")
        columns = {name.strip().lower(): name for name in reader.fieldnames if name}
        missing = [name for name in REQUIRED_COLUMNS if name not in columns]
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")

        bars: list[Bar] = []
        previous: datetime | None = None
        for row_number, row in enumerate(reader, start=2):
            try:
                timestamp = _parse_timestamp(row.get(columns["timestamp"]) or "")
                values = {
                    name: float(row[columns[name]])
                    for name in ("open", "high", "low", "close", "volume")
                }
                bar = Bar(timestamp=timestamp, **values)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"row {row_number}: {exc}") from exc
            if previous is not None and bar.timestamp <= previous:
                raise ValueError(
                    f"row {row_number}: timestamps must be strictly increasing and unique"
                )
            bars.append(bar)
            previous = bar.timestamp

    if not bars:
        raise ValueError("CSV contains no data rows")
    return tuple(bars)

