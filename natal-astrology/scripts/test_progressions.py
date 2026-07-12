import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.dirname(__file__))
pytest.importorskip("kerykeion")

from progressions import (  # noqa: E402
    _phase, build_progressions, render_markdown, main, PROG_ORB,
)

ABC = {
    "name": "ABC", "year": 2000, "month": 1, "day": 1, "hour": 12, "minute": 0,
    "lat": 51.5074, "lon": -0.1278, "tz": "Europe/London", "city": "London",
    "house_system": "Placidus",
}
PLANET_NAMES = {"Sun", "Moon", "Mercury", "Venus", "Mars",
                "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"}


def test_phase_math():
    assert _phase(0) == "New"
    assert _phase(45) == "Crescent"
    assert _phase(266.2) == "Disseminating"
    assert _phase(359) == "Balsamic"


def test_known_case():
    r = build_progressions(ABC, date(2026, 7, 2))
    assert r["points"]["prog Sun"]["sign"] == "Aquarius"
    assert r["points"]["prog Sun"]["natal_house"] == 11
    assert r["lunation"]["phase"] == "Disseminating"


def test_hits_wellformed():
    r = build_progressions(ABC, date(2026, 7, 2))
    assert r["hits"]
    for h in r["hits"]:
        assert h["a"].startswith("prog ")
        assert h["b"] in PLANET_NAMES | {"ASC", "MC"}
        assert h["type"] in {"conjunction", "sextile", "square", "trine", "opposition"}
        assert h["orb"] <= PROG_ORB
    assert any(h["a"] == "prog ASC" and h["type"] == "opposition" and h["b"] == "Jupiter"
               for h in r["hits"])


def test_structure():
    r = build_progressions(ABC, date(2026, 7, 2))
    assert set(r) == {"points", "lunation", "hits", "meta"}
    assert set(r["points"]) == {"prog Sun", "prog Moon", "prog Mercury", "prog Venus",
                                "prog Mars", "prog ASC", "prog MC"}
    for p in r["points"].values():
        assert 1 <= p["natal_house"] <= 12 and 0 <= p["degree"] < 30


def test_render_has_sections():
    md = render_markdown(build_progressions(ABC, date(2026, 7, 2)))
    assert "# Secondary Progressions" in md
    assert "## Progressed points" in md and "## Progressed lunation phase" in md
    assert "## Progressed-to-natal contacts" in md and "## Notes" in md


def test_cli_default_on(capsys):
    rc = main(["--name", "ABC", "--date", "2000-01-01", "--time", "12:00",
               "--lat", "51.5074", "--lon", "-0.1278", "--tz", "Europe/London", "--city", "London"])
    assert rc == 0
    assert "Progressed points" in capsys.readouterr().out


def test_cli_missing_time_flags(capsys):
    rc = main(["--name", "ABC", "--date", "2000-01-01",
               "--lat", "51.5074", "--lon", "-0.1278", "--tz", "Europe/London",
               "--city", "London", "--on", "2026-07-02"])
    assert rc == 0
    assert "Birth time unknown" in capsys.readouterr().out
