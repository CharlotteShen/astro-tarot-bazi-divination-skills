import os
import sys
from datetime import date, timedelta

import pytest

sys.path.insert(0, os.path.dirname(__file__))
pytest.importorskip("kerykeion")

from forecast import (  # noqa: E402
    _scan_series, _wrap180, find_forecast, EXACT_OFFSETS, FORECAST_MOVERS,
)

# Fake profile — not a real person.
ABC = {
    "name": "ABC", "year": 2000, "month": 1, "day": 1, "hour": 12, "minute": 0,
    "lat": 51.5074, "lon": -0.1278, "tz": "Europe/London", "city": "London",
    "house_system": "Placidus",
}
DAYS = [date(2026, 1, 1) + timedelta(days=k) for k in range(10)]


def test_scan_series_single_crossing():
    res = _scan_series(DAYS, [-3, -2, -1, -0.4, 0.3, 1, 2, 3, 4, 5], [False] * 10)
    assert len(res) == 1
    assert res[0]["rx"] is False
    enter, exit_ = res[0]["window"]
    assert enter <= res[0]["date"] <= exit_


def test_scan_series_retrograde_triple():
    signed = [-2, -0.5, 0.5, 0.6, 0.3, -0.5, -0.6, -0.3, 0.4, 1.5]
    retro = [False, False, False, True, True, True, False, False, False, False]
    res = _scan_series(DAYS, signed, retro)
    assert len(res) == 3
    assert [p["rx"] for p in res] == [False, True, False]


def test_scan_series_no_crossing():
    assert _scan_series(DAYS, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [False] * 10) == []


def test_exact_offsets_cover_five_aspects():
    assert set(EXACT_OFFSETS) == {"conjunction", "opposition", "trine", "square", "sextile"}
    for v in EXACT_OFFSETS.values():
        assert isinstance(v, list) and v and all(isinstance(o, int) for o in v)


def test_wrap180_and_signed_zero_at_exact():
    assert -180 <= _wrap180(200) < 180
    assert abs(_wrap180(0)) < 1e-9 and abs(_wrap180(360)) < 1e-9
    assert abs(_wrap180(50.0 - 50.0)) < 1e-9   # mover exactly at target+offset -> 0


def test_find_forecast_structure_sorted():
    r = find_forecast(ABC, "2026-07-01", "2026-10-01", True)
    entries = r["entries"]
    assert entries
    for e in entries:
        assert set(e) == {"mover", "target", "aspect", "exact_dates", "window"}
        assert e["mover"] in FORECAST_MOVERS
        assert e["exact_dates"]
        first = e["exact_dates"][0]["date"]
        assert e["window"][0] <= first <= e["window"][1]
    firsts = [e["exact_dates"][0]["date"] for e in entries]
    assert firsts == sorted(firsts)


def test_angles_suppressed_when_time_unknown():
    r = find_forecast(ABC, "2026-07-01", "2026-10-01", False)
    assert all(e["target"] not in ("ASC", "MC") for e in r["entries"])


from forecast import render_markdown, main  # noqa: E402


def test_render_has_both_groups():
    r = find_forecast(ABC, "2026-07-01", "2026-10-01", True)
    md = render_markdown(r)
    assert "## Major transits" in md and "## Mars triggers" in md
    mars_section = md.split("## Mars triggers")[1]
    major_section = md.split("## Major transits")[1].split("## Mars triggers")[0]
    assert "transiting Mars" in mars_section
    assert "transiting Mars" not in major_section


def test_cli_default_to_is_from_plus_365(capsys):
    rc = main(["--name", "ABC", "--date", "2000-01-01", "--time", "12:00",
               "--lat", "51.5074", "--lon", "-0.1278", "--tz", "Europe/London",
               "--city", "London", "--from", "2026-07-01"])
    assert rc == 0
    assert "2026-07-01 to 2027-07-01" in capsys.readouterr().out


def test_cli_reversed_range_errors(capsys):
    rc = main(["--name", "ABC", "--date", "2000-01-01", "--time", "12:00",
               "--lat", "51.5074", "--lon", "-0.1278", "--tz", "Europe/London",
               "--from", "2027-01-01", "--to", "2026-01-01"])
    assert rc == 1
    assert "Error" in capsys.readouterr().err


def test_cli_writes_report(tmp_path):
    out = tmp_path / "forecast.md"
    rc = main(["--name", "ABC", "--date", "2000-01-01", "--time", "12:00",
               "--lat", "51.5074", "--lon", "-0.1278", "--tz", "Europe/London",
               "--city", "London", "--from", "2026-07-01", "--to", "2026-09-01",
               "--out", str(out)])
    assert rc == 0
    assert out.exists() and out.stat().st_size > 0


def test_scan_series_ignores_wrap_discontinuity():
    # _wrap180 jumps +179 -> -179 at the 180deg anti-point; that jump is NOT a real perfection.
    signed = [178.5, 179.0, 179.5, -179.5, -179.0, -178.5, -178.0, -177.0, -176.0, -175.0]
    assert _scan_series(DAYS, signed, [False] * 10) == []


def test_scan_series_real_crossing_not_wrap_jump():
    # one real crossing (-0.5 -> 0.5) plus a wrap jump (179 -> -179); only the real one counts.
    signed = [-1.0, -0.5, 0.5, 1.0, 178.0, 179.0, -179.0, -178.0, -177.0, -176.0]
    res = _scan_series(DAYS, signed, [False] * 10)
    assert len(res) == 1
