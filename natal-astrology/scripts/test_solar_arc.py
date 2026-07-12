import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.dirname(__file__))
pytest.importorskip("kerykeion")

from solar_arc import _self_aspect, build_solar_arc, render_markdown, main, SA_ORB  # noqa: E402

ABC = {
    "name": "ABC", "year": 2000, "month": 1, "day": 1, "hour": 12, "minute": 0,
    "lat": 51.5074, "lon": -0.1278, "tz": "Europe/London", "city": "London",
    "house_system": "Placidus",
}
PLANET_NAMES = {"Sun", "Moon", "Mercury", "Venus", "Mars",
                "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"}


def test_self_aspect_math():
    sa = _self_aspect(60.5)
    assert sa == {"type": "sextile", "orb": 0.5}
    assert _self_aspect(27.0) is None
    assert _self_aspect(179.4) == {"type": "opposition", "orb": 0.6}


def test_known_case():
    r = build_solar_arc(ABC, date(2026, 7, 2))
    assert 26.9 <= r["meta"]["arc"] <= 27.1
    assert any(h["a"] == "SA Uranus" and h["type"] == "square" and h["b"] == "Pluto"
               and h["motion"] == "separating" for h in r["hits"])


def test_hits_wellformed_no_self_pairs():
    r = build_solar_arc(ABC, date(2026, 7, 2))
    for h in r["hits"]:
        assert h["a"].startswith("SA ")
        assert h["b"] in PLANET_NAMES | {"ASC", "MC"}
        assert h["a"] != f"SA {h['b']}"
        assert h["type"] in {"conjunction", "sextile", "square", "trine", "opposition"}
        assert h["orb"] <= SA_ORB
        assert h["motion"] in {"applying", "separating"}
        assert isinstance(h["months"], int) and h["months"] >= 0


def test_structure():
    r = build_solar_arc(ABC, date(2026, 7, 2))
    assert set(r) == {"hits", "self_aspect", "meta"}
    assert r["meta"]["rate"] > 0.9


def test_render_has_sections():
    md = render_markdown(build_solar_arc(ABC, date(2026, 7, 2)))
    assert "# Solar Arc Directions" in md
    assert "## Directed contacts" in md and "## Notes" in md


def test_cli_default_on(capsys):
    rc = main(["--name", "ABC", "--date", "2000-01-01", "--time", "12:00",
               "--lat", "51.5074", "--lon", "-0.1278", "--tz", "Europe/London", "--city", "London"])
    assert rc == 0
    assert "Directed contacts" in capsys.readouterr().out


def test_cli_missing_time_flags(capsys):
    rc = main(["--name", "ABC", "--date", "2000-01-01",
               "--lat", "51.5074", "--lon", "-0.1278", "--tz", "Europe/London",
               "--city", "London", "--on", "2026-07-02"])
    assert rc == 0
    assert "Birth time unknown" in capsys.readouterr().out
