import os
import sys
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.dirname(__file__))
pytest.importorskip("kerykeion")

from sensitivity import (  # noqa: E402
    analyze, PLANET_NAMES, COARSE_STEP_MINUTES,
    _range_offsets, _birth_at_offset, _bisect_flip, _snapshot,
)

BIRTH_UNKNOWN = {
    "name": "ABC", "year": 2000, "month": 1, "day": 1,
    "lat": 51.5074, "lon": -0.1278, "tz": "Europe/London", "city": "London",
    "house_system": "Placidus",
}


def test_range_offsets_midnight_crossing():
    base_dt, offsets = _range_offsets(BIRTH_UNKNOWN, "22:00", "02:00", COARSE_STEP_MINUTES)
    assert base_dt == datetime(2000, 1, 1, 22, 0)
    last_dt = base_dt + timedelta(minutes=offsets[-1])
    assert last_dt == datetime(2000, 1, 2, 2, 0)


def test_range_offsets_zero_width():
    base_dt, offsets = _range_offsets(BIRTH_UNKNOWN, "12:00", "12:00", COARSE_STEP_MINUTES)
    assert offsets == [0]


def test_wide_range_detects_asc_flip():
    result = analyze(BIRTH_UNKNOWN, "00:00", "23:00")
    assert "ASC_sign" in result["sensitive"]
    assert len(result["sensitive"]["ASC_sign"]) >= 2


def test_narrow_range_mostly_stable():
    # 00:00-00:10 has the Sun and Uranus crossing house cusps for this birth data — verified
    # programmatically that 09:00-09:10 is clear of any PLANET-HOUSE or Moon-sign crossing instead
    # (the two things this test checks). A derived point may still flip in some windows, which is
    # expected — this test only asserts "mostly stable", not "fully stable".
    result = analyze(BIRTH_UNKNOWN, "09:00", "09:10")
    for name in PLANET_NAMES:
        assert f"house_{name}" in result["stable"], (
            f"house_{name} unexpectedly sensitive in a 10-minute window")
    assert "Moon_sign" in result["stable"]


def test_zero_width_range():
    result = analyze(BIRTH_UNKNOWN, "12:00", "12:00")
    assert result["sensitive"] == {}
    assert len(result["stable"]) == 44


def test_bisection_precision():
    birth = BIRTH_UNKNOWN
    base_dt, offsets = _range_offsets(birth, "00:00", "23:00", COARSE_STEP_MINUTES)
    samples = [(off, _snapshot(_birth_at_offset(birth, base_dt, off))["ASC_sign"])
               for off in offsets]
    lo_off, lo_val = samples[0]
    hi_off = hi_val = None
    for off, val in samples[1:]:
        if val != lo_val:
            hi_off, hi_val = off, val
            break
    assert hi_off is not None, "expected at least one ASC sign flip in a 23h range"
    flip = _bisect_flip(birth, base_dt, lo_off, hi_off, "ASC_sign", lo_val)
    before = _snapshot(_birth_at_offset(birth, base_dt, flip - 1))["ASC_sign"]
    after = _snapshot(_birth_at_offset(birth, base_dt, flip))["ASC_sign"]
    assert before == lo_val and after == hi_val


from sensitivity import render_markdown, main  # noqa: E402


def test_render_markdown_has_sections():
    result = analyze(BIRTH_UNKNOWN, "00:00", "23:00")
    md = render_markdown(result, BIRTH_UNKNOWN, "00:00", "23:00")
    assert "## Stable" in md and "## Sensitive" in md and "## Takeaway" in md


def test_render_markdown_all_stable_takeaway(tmp_path):
    result = analyze(BIRTH_UNKNOWN, "12:00", "12:00")
    md = render_markdown(result, BIRTH_UNKNOWN, "12:00", "12:00")
    assert "stable across this entire range" in md


def test_cli_writes_report(tmp_path):
    out = tmp_path / "report.md"
    rc = main(["--name", "ABC", "--date", "2000-01-01", "--time-start", "06:00",
               "--time-end", "09:00", "--lat", "51.5074", "--lon", "-0.1278",
               "--tz", "Europe/London", "--city", "London", "--out", str(out)])
    assert rc == 0
    assert out.exists() and out.stat().st_size > 0


def test_cli_prints_when_no_out(capsys):
    rc = main(["--name", "ABC", "--date", "2000-01-01", "--time-start", "06:00",
               "--time-end", "06:05", "--lat", "51.5074", "--lon", "-0.1278",
               "--tz", "Europe/London", "--city", "London"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "## Stable" in out


def test_cli_invalid_date_errors(capsys):
    rc = main(["--date", "not-a-date", "--time-start", "06:00", "--time-end", "07:00",
               "--lat", "0", "--lon", "0", "--tz", "UTC"])
    assert rc == 1
    assert "Error" in capsys.readouterr().err
