"""Tests for the eLicznik CSV parser (no Home Assistant needed)."""

import importlib.util
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

# Load const.py and api.py without importing the package __init__ (which needs HA).
PKG = Path(__file__).parents[1] / "custom_components" / "tauron_energy"
sys.modules["tauron_energy"] = types.ModuleType("tauron_energy")
sys.modules["tauron_energy"].__path__ = [str(PKG)]
for name in ("const", "api"):
    spec = importlib.util.spec_from_file_location(f"tauron_energy.{name}", PKG / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

from tauron_energy.api import _is_csv, parse_csv  # noqa: E402

HEADER = "Data; Strefa; Wartość ;Rodzaj;Status;"


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


def test_partial_day_real_sample():
    # Captured from eLicznik on 2026-11-19 ~14:00 CET.
    text = "\n".join(
        [
            HEADER,
            "2026-11-19 1:00;T3;0,171;pobór [kWh]; licznik; ",
            "2026-11-19 2:00;T3;0,161;pobór [kWh]; licznik; ",
            "2026-11-19 6:00;T3;0,143;pobór [kWh]; licznik; ",
            "",
        ]
    )
    assert _is_csv(text)
    assert parse_csv(text) == [
        (utc(2026, 11, 18, 23), 0.171),  # 00:00-01:00 CET
        (utc(2026, 11, 19, 0), 0.161),
        (utc(2026, 11, 19, 4), 0.143),  # gap in the middle is kept as a gap
    ]


def test_spring_forward_day_has_23_hours():
    rows = [f"2026-03-29 {h}:00;T1;1,0;pobór [kWh]; licznik; " for h in range(1, 24)]
    result = parse_csv("\n".join([HEADER, *rows, "2026-03-30 1:00;T1;2,0;pobór [kWh]; licznik; "]))
    starts = [s for s, _ in result]
    assert starts[0] == utc(2026, 3, 28, 23)  # midnight CET
    assert starts[22] == utc(2026, 3, 29, 21)  # 23rd hour ends at local midnight (CEST)
    assert starts[23] == utc(2026, 3, 29, 22)  # next day's first hour, contiguous
    assert len(set(starts)) == 24


def test_autumn_back_day_has_25_hours():
    rows = [f"2026-10-25 {h}:00;T1;1,0;pobór [kWh]; licznik; " for h in range(1, 26)]
    result = parse_csv("\n".join([HEADER, *rows, "2026-10-26 1:00;T1;2,0;pobór [kWh]; licznik; "]))
    starts = [s for s, _ in result]
    assert starts[0] == utc(2026, 10, 24, 22)  # midnight CEST
    assert starts[24] == utc(2026, 10, 25, 22)
    assert starts[25] == utc(2026, 10, 25, 23)  # next day's midnight CET, contiguous
    assert len(set(starts)) == 26


def test_repeated_label_becomes_next_hour():
    text = "\n".join(
        [
            HEADER,
            "2026-10-25 2:00;T1;1,0;pobór [kWh]; licznik; ",
            "2026-10-25 3:00;T1;1,0;pobór [kWh]; licznik; ",
            "2026-10-25 3:00;T1;1,0;pobór [kWh]; licznik; ",
        ]
    )
    starts = [s for s, _ in parse_csv(text)]
    assert starts == [utc(2026, 10, 24, 23), utc(2026, 10, 25, 0), utc(2026, 10, 25, 1)]


def test_html_page_is_not_csv():
    assert not _is_csv("<!DOCTYPE html><html>login</html>")
