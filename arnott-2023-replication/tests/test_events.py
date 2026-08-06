import pandas as pd

from arnott_replication.events import build_membership_events, summarize_event_counts


def test_membership_diff_uses_previously_known_schedule() -> None:
    constituents = pd.DataFrame(
        {
            "일자": ["2024-06-12", "2024-06-12", "2024-06-13", "2024-06-13"],
            "적용일": ["2024-06-13", "2024-06-13", "2024-06-14", "2024-06-14"],
            "종목코드2": ["A000001", "A000002", "A000002", "A000003"],
            "종목명국문": ["one", "two", "two", "three"],
            "지수내비중": [".4", ".6", ".5", ".5"],
        }
    )
    levels = pd.DataFrame(
        {
            "VALUE_DATE": ["2024-06-12", "2024-06-13"],
            "NEXT_REBALANCE_DATE": ["2024-06-14", "2024-12-13"],
        }
    )
    events = build_membership_events(constituents, levels)
    assert list(events["action"]) == ["addition", "deletion"]
    assert set(events["ticker"]) == {"A000001", "A000003"}
    assert events["is_scheduled"].all()
    assert events["announcement_date"].isna().all()
    counts = summarize_event_counts(events)
    assert counts.iloc[0].to_dict() == {
        "year": 2024,
        "event_groups": 1,
        "additions": 1,
        "deletions": 1,
    }


def test_unscheduled_change_is_excluded_by_default() -> None:
    constituents = pd.DataFrame(
        {
            "일자": ["2024-01-02", "2024-01-02", "2024-01-03", "2024-01-03"],
            "적용일": ["2024-01-03", "2024-01-03", "2024-01-04", "2024-01-04"],
            "종목코드2": ["A", "B", "B", "C"],
            "종목명국문": ["A", "B", "B", "C"],
            "지수내비중": [".5", ".5", ".5", ".5"],
        }
    )
    levels = pd.DataFrame(
        {
            "VALUE_DATE": ["2024-01-02"],
            "NEXT_REBALANCE_DATE": ["2024-06-14"],
        }
    )
    assert build_membership_events(constituents, levels).empty
