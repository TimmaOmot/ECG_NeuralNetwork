from __future__ import annotations

import pytest

from src.data.labels import (
    ABNORMAL,
    NORMAL,
    V2_CLASSES,
    map_v1,
    map_v2,
    summarize_counts,
)

# The ADR 0003 mapping table, spelled out symbol by symbol.
V1_TABLE = {
    "N": NORMAL, "L": NORMAL, "R": NORMAL, "e": NORMAL, "j": NORMAL,
    "A": ABNORMAL, "a": ABNORMAL, "J": ABNORMAL, "S": ABNORMAL,
    "V": ABNORMAL, "E": ABNORMAL, "F": ABNORMAL,
}
V2_TABLE = {
    "N": "N", "L": "N", "R": "N", "e": "N", "j": "N",
    "A": "S", "a": "S", "J": "S", "S": "S",
    "V": "V", "E": "V",
    "F": "F",
    "/": "Q", "f": "Q", "Q": "Q",
}
# Non-beat / rhythm / quality markers and V1-excluded beat symbols.
EXCLUDED_FROM_V1 = ["/", "f", "Q", "+", "~", "!", '"', "|", "x", "[", "]"]


@pytest.mark.parametrize("symbol,expected", V1_TABLE.items())
def test_map_v1_matches_the_adr_table(symbol: str, expected: str) -> None:
    assert map_v1(symbol) == expected


@pytest.mark.parametrize("symbol", EXCLUDED_FROM_V1)
def test_map_v1_excludes_paced_and_non_beat_symbols(symbol: str) -> None:
    assert map_v1(symbol) is None


@pytest.mark.parametrize("symbol,expected", V2_TABLE.items())
def test_map_v2_matches_the_superclass_table(symbol: str, expected: str) -> None:
    assert map_v2(symbol) == expected


@pytest.mark.parametrize("symbol", ["+", "~", "!", '"', "|", "x", "[", "]"])
def test_map_v2_excludes_non_beat_symbols(symbol: str) -> None:
    assert map_v2(symbol) is None


def test_v2_normal_grouping_is_identical_to_v1_normal() -> None:
    for symbol in ("N", "L", "R", "e", "j"):
        assert map_v1(symbol) == NORMAL
        assert map_v2(symbol) == "N"


def test_summarize_counts_aggregates_v1_v2_and_excluded() -> None:
    counts = {
        "N": 100, "L": 10, "R": 5,  # -> Normal / N
        "V": 8, "E": 1,             # -> Abnormal / V
        "A": 4,                     # -> Abnormal / S
        "F": 2,                     # -> Abnormal / F
        "/": 20, "f": 3,            # -> excluded in V1, Q in V2
        "+": 7, "~": 1,            # -> excluded everywhere
    }
    summary = summarize_counts(counts)

    assert summary["v1"] == {NORMAL: 115, ABNORMAL: 15}
    assert summary["v1_included_total"] == 130
    assert summary["v2"] == {"N": 115, "S": 4, "V": 9, "F": 2, "Q": 23}
    assert summary["v2_included_total"] == 153
    # "excluded" is the V1 view: paced/fusion/unclassifiable beats plus non-beat markers.
    assert summary["excluded_by_symbol"] == {"+": 7, "/": 20, "f": 3, "~": 1}
    assert summary["excluded_total"] == 31
    # V2 recovers / and f (but not the + and ~ non-beat markers) into class Q.
    assert summary["v2_recovered_total"] == 23


def test_summarize_counts_handles_an_empty_map() -> None:
    summary = summarize_counts({})
    assert summary["v1"] == {NORMAL: 0, ABNORMAL: 0}
    assert summary["v2"] == {klass: 0 for klass in V2_CLASSES}
    assert summary["excluded_total"] == 0
