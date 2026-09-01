"""V1/V2 beat-label mapping for MIT-BIH annotation symbols.

The mapping is a documented benchmark convention, fixed in
``docs/adr/0003-explicit-v1-label-mapping.md``. Symbols outside the mapping are
*excluded*: they never become a training or evaluation example and are never
folded into the abnormal class.
"""

from __future__ import annotations

from collections.abc import Mapping

# --- V1 binary target -----------------------------------------------------------

V1_NORMAL_SYMBOLS = frozenset({"N", "L", "R", "e", "j"})
V1_ABNORMAL_SYMBOLS = frozenset({"A", "a", "J", "S", "V", "E", "F"})

NORMAL = "Normal"
ABNORMAL = "Abnormal"

# --- V2 five-class superclasses ------------------------------------------------
# N, S, V, F, Q. V2 keeps the V1 normal grouping and adds the paced/unclassifiable
# Q bucket that V1 excludes.

V2_SUPERCLASS_BY_SYMBOL: dict[str, str] = {
    **{symbol: "N" for symbol in ("N", "L", "R", "e", "j")},
    **{symbol: "S" for symbol in ("A", "a", "J", "S")},
    **{symbol: "V" for symbol in ("V", "E")},
    "F": "F",
    **{symbol: "Q" for symbol in ("/", "f", "Q")},
}

V2_CLASSES = ("N", "S", "V", "F", "Q")

# Beat symbols the project deliberately excludes from V1 (paced, fusion-paced,
# unclassifiable). Listed for reporting; any symbol not otherwise mapped is also
# excluded, including every non-beat/rhythm/quality marker (``+ ~ ! " | x [ ]``).
V1_EXCLUDED_BEAT_SYMBOLS = frozenset({"/", "f", "Q"})


def map_v1(symbol: str) -> str | None:
    """Return ``"Normal"``, ``"Abnormal"``, or ``None`` when the symbol is excluded."""
    if symbol in V1_NORMAL_SYMBOLS:
        return NORMAL
    if symbol in V1_ABNORMAL_SYMBOLS:
        return ABNORMAL
    return None


def map_v2(symbol: str) -> str | None:
    """Return the N/S/V/F/Q superclass, or ``None`` when the symbol is excluded."""
    return V2_SUPERCLASS_BY_SYMBOL.get(symbol)


def summarize_counts(counts_by_symbol: Mapping[str, int]) -> dict[str, object]:
    """Aggregate a per-symbol count map (as stored in the inventory manifest).

    Returns pooled V1 and V2 class counts plus the excluded-symbol breakdown, so
    callers never re-read WFDB files just to report distributions. "Excluded"
    here is the V1 view (``map_v1`` returns ``None``); V2 recovers ``/``, ``f``,
    and ``Q`` into its ``Q`` class, so ``v2_recovered_total`` reports how many of
    the V1-excluded annotations V2 keeps.
    """
    v1: dict[str, int] = {NORMAL: 0, ABNORMAL: 0}
    v2: dict[str, int] = {klass: 0 for klass in V2_CLASSES}
    excluded: dict[str, int] = {}
    v2_recovered = 0

    for symbol, count in counts_by_symbol.items():
        v1_class = map_v1(symbol)
        v2_class = map_v2(symbol)
        if v1_class is not None:
            v1[v1_class] += count
        if v2_class is not None:
            v2[v2_class] += count
        if v1_class is None:
            excluded[symbol] = excluded.get(symbol, 0) + count
            if v2_class is not None:
                v2_recovered += count

    return {
        "v1": v1,
        "v1_included_total": v1[NORMAL] + v1[ABNORMAL],
        "v2": v2,
        "v2_included_total": sum(v2.values()),
        "excluded_by_symbol": dict(sorted(excluded.items())),
        "excluded_total": sum(excluded.values()),
        "v2_recovered_total": v2_recovered,
    }
