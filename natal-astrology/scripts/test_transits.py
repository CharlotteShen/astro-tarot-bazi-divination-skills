import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
pytest.importorskip("kerykeion")

from chart import build_chart_data  # noqa: E402
from transits import (  # noqa: E402
    _positions, _aspect_between, _natal_targets, find_transits, MOVERS,
)

# Fake profile — not a real person.
ABC = {
    "name": "ABC", "year": 2000, "month": 1, "day": 1, "hour": 12, "minute": 0,
    "lat": 51.5074, "lon": -0.1278, "tz": "Europe/London", "city": "London",
    "house_system": "Placidus",
}
ON = "2026-07-01"


def test_positions_includes_chiron_node():
    pos = _positions(ON, 51.5074, -0.1278, "Europe/London")
    assert set(pos) == set(MOVERS)
    assert "Chiron" in pos and "North Node" in pos
    for v in pos.values():
        assert 0 <= v < 360


def test_aspect_between_tight_orb():
    assert _aspect_between(10.0, 10.0, False) == ("conjunction", 0.0)
    assert _aspect_between(10.0, 15.0, False) is None   # 5° apart > 3° transit orb


def test_moon_wider_orb():
    assert _aspect_between(10.0, 14.0, True) is not None     # 4° <= 3+2 (Moon bonus)
    assert _aspect_between(10.0, 14.0, False) is None        # 4° > 3 for non-Moon


def test_find_transits_structure_and_motion():
    tr = find_transits(ABC, ON, True)
    assert tr, "expected some transits for this fixture/date"
    targets_ok = set(MOVERS) | {"ASC", "MC"}
    for t in tr:
        assert set(t) == {"mover", "type", "target", "orb", "motion"}
        assert t["mover"] in MOVERS
        assert t["target"] in targets_ok
        assert t["motion"] in {"applying", "separating"}
        assert t["type"] in {"conjunction", "sextile", "square", "trine", "opposition"}


def test_angles_suppressed_when_time_unknown():
    cd = build_chart_data(ABC)
    targets = _natal_targets(cd, birth_time_known=False)
    assert "ASC" not in targets and "MC" not in targets
    tr = find_transits(ABC, ON, False)
    assert all(t["target"] not in ("ASC", "MC") for t in tr)


def test_angles_present_when_time_known():
    cd = build_chart_data(ABC)
    targets = _natal_targets(cd, birth_time_known=True)
    assert "ASC" in targets and "MC" in targets


from datetime import date  # noqa: E402

from transits import render_markdown, main  # noqa: E402


def test_render_has_groups_and_notes():
    tr = find_transits(ABC, ON, True)
    meta = {"name": "ABC", "on": ON, "natal_date": "2000-01-01", "city": "London",
            "birth_time_known": True}
    md = render_markdown(tr, meta)
    assert "# Transits for ABC — 2026-07-01" in md
    assert "## Slow / outer transits" in md and "## Fast / inner transits" in md
    assert "## Notes" in md and "Moon" in md


def test_cli_default_on_is_today(capsys):
    rc = main(["--name", "ABC", "--date", "2000-01-01", "--time", "12:00",
               "--lat", "51.5074", "--lon", "-0.1278", "--tz", "Europe/London",
               "--city", "London"])
    assert rc == 0
    out = capsys.readouterr().out
    assert date.today().isoformat() in out


def test_cli_writes_report(tmp_path):
    out = tmp_path / "transits.md"
    rc = main(["--name", "ABC", "--date", "2000-01-01", "--time", "12:00",
               "--lat", "51.5074", "--lon", "-0.1278", "--tz", "Europe/London",
               "--city", "London", "--on", ON, "--out", str(out)])
    assert rc == 0
    assert out.exists() and out.stat().st_size > 0


def test_cli_missing_time_suppresses_angles(capsys):
    rc = main(["--name", "ABC", "--date", "2000-01-01",
               "--lat", "51.5074", "--lon", "-0.1278", "--tz", "Europe/London",
               "--city", "London", "--on", ON])
    assert rc == 0
    out = capsys.readouterr().out
    assert "natal ASC" not in out and "natal MC" not in out
    assert "Natal birth time unknown" in out
