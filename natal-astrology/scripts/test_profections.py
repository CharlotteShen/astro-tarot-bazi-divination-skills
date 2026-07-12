import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.dirname(__file__))
pytest.importorskip("kerykeion")

from profections import (  # noqa: E402
    annual_profection, monthly_profection, build_profections, render_markdown, main, _age_on,
)

ABC = {
    "name": "ABC", "year": 2000, "month": 1, "day": 1, "hour": 12, "minute": 0,
    "lat": 51.5074, "lon": -0.1278, "tz": "Europe/London", "city": "London",
    "house_system": "Placidus",
}


def test_annual_age0_is_first_house():
    assert annual_profection("Aries", 0) == {"house": 1, "sign": "Aries", "lord": "Mars"}
    assert annual_profection("Aries", 12)["house"] == 1   # 12-year cycle


def test_annual_known_case():
    assert annual_profection("Aries", 26) == {"house": 3, "sign": "Gemini", "lord": "Mercury"}


def test_monthly_wraps():
    assert monthly_profection("Aries", 3, 0)["house"] == 3     # birthday month = annual house
    assert monthly_profection("Aries", 3, 11)["house"] == 2    # last month = house before annual


def test_age_on_birthday_boundary():
    assert _age_on(date(2000, 1, 1), date(2026, 1, 1)) == 26
    assert _age_on(date(2000, 1, 1), date(2025, 12, 31)) == 25


def test_build_structure():
    r = build_profections(ABC, date(2026, 7, 2))
    assert set(r) == {"ref_date", "year_window", "annual", "monthly", "meta"}
    a = r["annual"]
    assert set(a) >= {"house", "sign", "lord", "lord_placement", "activated"}
    assert isinstance(a["lord_placement"], tuple) and len(a["lord_placement"]) == 2
    assert isinstance(a["activated"], list)
    assert 1 <= r["monthly"]["house"] <= 12


def test_render_has_sections():
    md = render_markdown(build_profections(ABC, date(2026, 7, 2)))
    assert "# Annual Profection" in md
    assert "## This year" in md and "## This month" in md and "## Notes" in md


def test_cli_default_on(capsys):
    rc = main(["--name", "ABC", "--date", "2000-01-01", "--time", "12:00",
               "--lat", "51.5074", "--lon", "-0.1278", "--tz", "Europe/London", "--city", "London"])
    assert rc == 0
    assert "Profected house" in capsys.readouterr().out


def test_cli_missing_time_flags(capsys):
    rc = main(["--name", "ABC", "--date", "2000-01-01",
               "--lat", "51.5074", "--lon", "-0.1278", "--tz", "Europe/London",
               "--city", "London", "--on", "2026-07-02"])
    assert rc == 0
    assert "Birth time unknown" in capsys.readouterr().out
