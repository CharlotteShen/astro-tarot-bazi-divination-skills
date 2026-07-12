import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
pytest.importorskip("kerykeion")

from sensitivity import _abs  # noqa: E402
from solar_return import build_solar_return, SR_TO_NATAL_ORB  # noqa: E402

ABC = {
    "name": "ABC", "year": 2000, "month": 1, "day": 1, "hour": 12, "minute": 0,
    "lat": 51.5074, "lon": -0.1278, "tz": "Europe/London", "city": "London",
    "house_system": "Placidus",
}
PLANET_NAMES = {"Sun", "Moon", "Mercury", "Venus", "Mars",
                "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"}


def _sun_abs(cd):
    p = next(x for x in cd["planets"] if x["body"] == "Sun")
    return _abs(p["sign"], p["degree"])


def test_sr_sun_returns_to_natal():
    from chart import build_chart_data
    natal_sun = _sun_abs(build_chart_data(ABC))
    r = build_solar_return(ABC, 2026)
    sr_sun = _sun_abs(r["sr_chart"])
    assert min(abs(sr_sun - natal_sun), 360 - abs(sr_sun - natal_sun)) < (1 / 60.0)


def test_sr_structure():
    r = build_solar_return(ABC, 2026)
    assert set(r) >= {"sr_utc", "sr_local", "location", "sr_chart", "bridge", "meta"}
    assert "planets" in r["sr_chart"] and "angles" in r["sr_chart"]
    assert set(r["bridge"]) == {"overlay", "contacts"}


def test_bridge_overlay_houses():
    r = build_solar_return(ABC, 2026)
    ov = r["bridge"]["overlay"]
    assert set(ov) == {"SR ASC", "SR MC", "SR Sun", "SR Moon"}
    for h in ov.values():
        assert 1 <= h <= 12


def test_bridge_contacts_wellformed():
    r = build_solar_return(ABC, 2026)
    for c in r["bridge"]["contacts"]:
        assert c["a"] in {"SR ASC", "SR MC", "SR Sun", "SR Moon"}
        assert c["b"] in PLANET_NAMES | {"ASC", "MC"}
        assert c["type"] in {"conjunction", "sextile", "square", "trine", "opposition"}
        assert c["orb"] <= SR_TO_NATAL_ORB


def test_relocated_changes_angles_not_sun():
    home = build_solar_return(ABC, 2026)
    ny = build_solar_return(ABC, 2026, sr_location={
        "lat": 40.71, "lon": -74.01, "tz": "America/New_York", "city": "New York"})
    assert _sun_abs(ny["sr_chart"]) == _sun_abs(home["sr_chart"])   # same instant
    assert ny["sr_chart"]["angles"]["ASC"] != home["sr_chart"]["angles"]["ASC"]
    assert ny["location"]["relocated"] is True


from datetime import date  # noqa: E402

from solar_return import render_markdown, main  # noqa: E402


def test_render_has_sections():
    md = render_markdown(build_solar_return(ABC, 2026))
    assert "# Solar Return 2026 — ABC" in md
    assert "## The year's chart" in md and "## Bridge to your natal chart" in md
    assert "## Notes" in md


def test_cli_default_year(capsys):
    rc = main(["--name", "ABC", "--date", "2000-01-01", "--time", "12:00",
               "--lat", "51.5074", "--lon", "-0.1278", "--tz", "Europe/London", "--city", "London"])
    assert rc == 0
    assert f"Solar Return {date.today().year}" in capsys.readouterr().out


def test_cli_missing_time_flags(capsys):
    rc = main(["--name", "ABC", "--date", "2000-01-01",
               "--lat", "51.5074", "--lon", "-0.1278", "--tz", "Europe/London",
               "--city", "London", "--year", "2026"])
    assert rc == 0
    assert "Natal birth time unknown" in capsys.readouterr().out


def test_cli_partial_location_errors(capsys):
    rc = main(["--name", "ABC", "--date", "2000-01-01", "--time", "12:00",
               "--lat", "51.5074", "--lon", "-0.1278", "--tz", "Europe/London",
               "--year", "2026", "--loc-lat", "40.71"])   # missing --loc-lon/--loc-tz
    assert rc == 1
    assert "Error" in capsys.readouterr().err
