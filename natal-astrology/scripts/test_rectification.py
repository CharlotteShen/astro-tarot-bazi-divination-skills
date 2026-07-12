import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.dirname(__file__))
pytest.importorskip("kerykeion")

from rectification import (  # noqa: E402
    _progressed_birth, _transit_positions, _hits, score_candidate, analyze,
    PLANET_NAMES,
)

# Fake profile — not a real person.
BIRTH = {
    "name": "ABC", "year": 2000, "month": 1, "day": 1,
    "lat": 51.5074, "lon": -0.1278, "tz": "Europe/London", "city": "London",
    "house_system": "Placidus",
}
EVENTS = [
    {"date": "2020-03-15", "label": "started my current job"},
    {"date": "2022-08-01", "label": "moved abroad"},
]


def test_progressed_birth_shifts_date():
    birth = dict(BIRTH, hour=12, minute=0)
    pb = _progressed_birth(birth, "2030-01-01")  # ~30 years after birth
    days = (date(pb["year"], pb["month"], pb["day"]) - date(2000, 1, 1)).days
    assert 28 <= days <= 32   # day-for-a-year: ~30 days after birth
    # a fractional age shifts hour/minute off the birth's 12:00 (not truncated to whole days)
    pb2 = _progressed_birth(birth, "2030-07-02")  # ~30.5 years -> +~30.5 days -> +~12h
    assert (pb2["hour"], pb2["minute"]) != (12, 0)


def test_transit_positions_returns_ten_planets():
    pos = _transit_positions("2020-03-15", 51.5074, -0.1278, "Europe/London")
    assert set(pos) == set(PLANET_NAMES)
    for v in pos.values():
        assert 0 <= v < 360


def test_hits_finds_known_aspect():
    hit = _hits({"X": 10.0}, {"Y": 10.0}, "progressed")
    assert len(hit) == 1
    assert hit[0]["type"] == "conjunction" and hit[0]["orb"] < 0.01
    assert hit[0]["kind"] == "progressed" and hit[0]["moving"] == "X" and hit[0]["target"] == "Y"
    assert _hits({"X": 10.0}, {"Y": 55.0}, "transit") == []   # 45° apart = no defined aspect


def test_score_candidate_nonnegative_and_structured():
    cand = dict(BIRTH, hour=9, minute=0)
    tc = [_transit_positions(e["date"], BIRTH["lat"], BIRTH["lon"], BIRTH["tz"]) for e in EVENTS]
    sc = score_candidate(cand, EVENTS, tc)
    assert isinstance(sc["score"], int) and sc["score"] >= 0
    assert len(sc["events"]) == len(EVENTS)
    for ev in sc["events"]:
        assert {"date", "label", "hits"} <= set(ev)
        assert isinstance(ev["hits"], list)


def test_analyze_ranks_descending():
    result = analyze(BIRTH, "09:00", "10:00", EVENTS)
    ranked = result["ranked"]
    assert len(ranked) == 5   # 09:00, 09:15, 09:30, 09:45, 10:00
    for a, b in zip(ranked, ranked[1:]):
        assert a["score"] >= b["score"]
    assert result["meta"]["candidate_count"] == 5


from rectification import render_markdown, main  # noqa: E402


def test_render_markdown_has_sections():
    result = analyze(BIRTH, "09:00", "10:00", EVENTS)
    md = render_markdown(result, BIRTH, "09:00", "10:00", EVENTS)
    assert "# Rectification report — ABC" in md
    assert "## Ranked candidate times" in md and "## Caveat" in md
    # each supplied event label should appear in the "Events considered" header block
    assert "started my current job" in md and "moved abroad" in md


def test_cli_requires_at_least_one_event(capsys):
    rc = main(["--name", "ABC", "--date", "2000-01-01", "--time-start", "09:00",
               "--time-end", "10:00", "--lat", "51.5074", "--lon", "-0.1278",
               "--tz", "Europe/London", "--city", "London"])
    assert rc == 1
    assert "event" in capsys.readouterr().err.lower()


def test_cli_parses_multiple_events(capsys):
    rc = main(["--name", "ABC", "--date", "2000-01-01", "--time-start", "09:00",
               "--time-end", "10:00", "--lat", "51.5074", "--lon", "-0.1278",
               "--tz", "Europe/London", "--city", "London",
               "--event", "2020-03-15:started my current job",
               "--event", "2022-08-01:moved abroad"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "started my current job" in out and "moved abroad" in out
    assert "## Ranked candidate times" in out
