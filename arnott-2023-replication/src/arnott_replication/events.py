"""Recover KOSPI200 additions and deletions from adjacent membership snapshots."""

from __future__ import annotations

import numpy as np
import pandas as pd


CONSTITUENT_COLUMNS = {
    "일자",
    "적용일",
    "종목코드2",
    "종목명국문",
    "지수내비중",
}
INDEX_COLUMNS = {"VALUE_DATE", "NEXT_REBALANCE_DATE"}


def _require_columns(frame: pd.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{label} is missing columns: {missing}")


def _numeric_weight(value: object) -> float:
    parsed = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return float(parsed) if pd.notna(parsed) else np.nan


def build_membership_events(
    constituents: pd.DataFrame,
    index_levels: pd.DataFrame,
    *,
    scheduled_only: bool = True,
    require_both_sides: bool = True,
) -> pd.DataFrame:
    """Diff consecutive snapshots and identify scheduled effective dates.

    `NEXT_REBALANCE_DATE` is used only if it was already present before the
    membership-changing snapshot. `CHANGED_GB` is intentionally ignored.
    """

    _require_columns(constituents, CONSTITUENT_COLUMNS, "constituents")
    _require_columns(index_levels, INDEX_COLUMNS, "index_levels")
    members = constituents[list(CONSTITUENT_COLUMNS)].copy()
    members["일자"] = pd.to_datetime(members["일자"], errors="raise").dt.normalize()
    members["적용일"] = pd.to_datetime(members["적용일"], errors="raise").dt.normalize()
    members["종목코드2"] = members["종목코드2"].astype("string").str.strip()
    members = members.dropna(subset=["일자", "적용일", "종목코드2"])
    if members.duplicated(["일자", "종목코드2"]).any():
        raise ValueError("Constituent snapshots have duplicate date-ticker keys")

    schedule = index_levels[list(INDEX_COLUMNS)].copy()
    schedule["VALUE_DATE"] = pd.to_datetime(
        schedule["VALUE_DATE"], errors="raise"
    ).dt.normalize()
    schedule["NEXT_REBALANCE_DATE"] = pd.to_datetime(
        schedule["NEXT_REBALANCE_DATE"], errors="coerce"
    ).dt.normalize()

    by_date = {date: group.set_index("종목코드2") for date, group in members.groupby("일자")}
    dates = sorted(by_date)
    records: list[dict[str, object]] = []
    for previous_date, snapshot_date in zip(dates[:-1], dates[1:], strict=True):
        previous = by_date[previous_date]
        current = by_date[snapshot_date]
        previous_tickers = set(previous.index)
        current_tickers = set(current.index)
        additions = sorted(current_tickers - previous_tickers)
        deletions = sorted(previous_tickers - current_tickers)
        if not additions and not deletions:
            continue
        effective_values = current["적용일"].dropna().mode()
        if effective_values.empty:
            raise ValueError(f"No effective date for snapshot {snapshot_date.date()}")
        effective_date = effective_values.iloc[0]
        known_schedule = set(
            schedule.loc[
                schedule["VALUE_DATE"].le(previous_date), "NEXT_REBALANCE_DATE"
            ].dropna()
        )
        is_scheduled = effective_date in known_schedule
        if scheduled_only and not is_scheduled:
            continue
        if require_both_sides and (not additions or not deletions):
            continue
        event_id = f"{effective_date:%Y%m%d}"
        for action, tickers, source in (
            ("addition", additions, current),
            ("deletion", deletions, previous),
        ):
            for ticker in tickers:
                row = source.loc[ticker]
                records.append(
                    {
                        "event_id": event_id,
                        "previous_snapshot_date": previous_date,
                        "snapshot_date": snapshot_date,
                        "effective_date": effective_date,
                        "is_scheduled": is_scheduled,
                        "action": action,
                        "ticker": ticker,
                        "ticker_name": row["종목명국문"],
                        "index_weight_pct": _numeric_weight(row["지수내비중"]),
                        "announcement_date": pd.NaT,
                        "change_reason": pd.NA,
                    }
                )
    columns = [
        "event_id",
        "previous_snapshot_date",
        "snapshot_date",
        "effective_date",
        "is_scheduled",
        "action",
        "ticker",
        "ticker_name",
        "index_weight_pct",
        "announcement_date",
        "change_reason",
    ]
    result = pd.DataFrame.from_records(records, columns=columns)
    if result.empty:
        return result
    return result.sort_values(["effective_date", "action", "ticker"]).reset_index(
        drop=True
    )


def summarize_event_counts(events: pd.DataFrame) -> pd.DataFrame:
    """Count event groups and constituent changes by calendar year."""

    if events.empty:
        return pd.DataFrame(
            columns=["year", "event_groups", "additions", "deletions"]
        )
    frame = events.copy()
    frame["year"] = pd.to_datetime(frame["effective_date"]).dt.year
    counts = (
        frame.groupby(["year", "action"]).size().unstack(fill_value=0).reset_index()
    )
    for action in ("addition", "deletion"):
        if action not in counts:
            counts[action] = 0
    groups = frame.groupby("year")["event_id"].nunique().rename("event_groups")
    counts = counts.merge(groups, on="year", validate="one_to_one")
    return counts.rename(
        columns={"addition": "additions", "deletion": "deletions"}
    )[["year", "event_groups", "additions", "deletions"]]
