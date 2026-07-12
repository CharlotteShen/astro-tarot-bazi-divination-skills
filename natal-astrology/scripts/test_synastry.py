import io
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
pytest.importorskip("kerykeion")

from synastry import build_synastry_data, midpoint, find_house, find_reinforced, main  # noqa: E402

BIRTH_A = {"name": "A", "year": 1990, "month": 3, "day": 15, "hour": 14, "minute": 30,
           "lat": 39.90, "lon": 116.41, "tz": "Asia/Shanghai", "city": "Beijing",
           "house_system": "Placidus"}
BIRTH_B = {"name": "B", "year": 1988, "month": 11, "day": 5, "hour": 18, "minute": 45,
           "lat": 31.23, "lon": 121.47, "tz": "Asia/Shanghai", "city": "Shanghai",
           "house_system": "Placidus"}

PLANETS = {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
           "Uranus", "Neptune", "Pluto"}
MAJORS = {"conjunction", "sextile", "square", "trine", "opposition"}


def test_midpoint_nearer_arc():
    assert midpoint(10.0, 50.0) == pytest.approx(30.0)
    assert midpoint(350.0, 30.0) == pytest.approx(10.0)  # wraps the short way


def test_inter_aspects_well_formed():
    sd = build_synastry_data(BIRTH_A, BIRTH_B, "romantic")
    assert sd["relationship_type"] == "romantic"
    assert sd["inter_aspects"]
    for a in sd["inter_aspects"]:
        assert a["a"].startswith("A.") and a["b"].startswith("B.")
        assert a["type"] in MAJORS
        assert a["orb"] <= 8


def test_overlays_cover_all_planets():
    sd = build_synastry_data(BIRTH_A, BIRTH_B, "work")
    a_planets = {o["planet"].split(".")[1] for o in sd["overlays"]["a_in_b"]}
    b_planets = {o["planet"].split(".")[1] for o in sd["overlays"]["b_in_a"]}
    assert a_planets == PLANETS and b_planets == PLANETS
    for o in sd["overlays"]["a_in_b"] + sd["overlays"]["b_in_a"]:
        assert 1 <= o["house"] <= 12


def test_composite_shape():
    sd = build_synastry_data(BIRTH_A, BIRTH_B, "friendship")
    comp = sd["composite"]
    assert {p["body"] for p in comp["planets"]} == PLANETS
    for p in comp["planets"]:
        assert 0 <= p["degree"] < 30 and 1 <= p["house"] <= 12 and p["sign"]
    assert comp["angles"]["ASC"]["sign"] and comp["angles"]["MC"]["sign"]
    for a in comp["aspects"]:
        assert a["type"] in MAJORS and a["orb"] <= 8


def test_default_relationship_type():
    sd = build_synastry_data(BIRTH_A, BIRTH_B)
    assert sd["relationship_type"] == "romantic"


def test_find_house_wraps_zero_aries():
    # 12 equal houses starting at 20° Aries; house 12 spans 350°→20° across 0° Aries.
    cusps = [20, 50, 80, 110, 140, 170, 200, 230, 260, 290, 320, 350]
    assert find_house(355, cusps) == 12   # just before the wrap
    assert find_house(5, cusps) == 12     # just after 0°, still house 12
    assert find_house(25, cusps) == 1     # house 1 starts at 20°
    assert find_house(140, cusps) == 5    # exactly on the 5th cusp


def test_find_reinforced_double_whammy():
    ia = [{"a": "A.Sun", "type": "conjunction", "b": "B.Moon", "orb": 1.0},
          {"a": "A.Moon", "type": "trine", "b": "B.Sun", "orb": 2.0}]
    r = find_reinforced(ia)
    assert len(r["double_whammies"]) == 1
    dw = r["double_whammies"][0]
    assert dw["pair"] == ["Moon", "Sun"]
    assert len(dw["aspects"]) == 2


def test_find_reinforced_no_false_double_whammy():
    ia = [{"a": "A.Sun", "type": "conjunction", "b": "B.Moon", "orb": 1.0}]
    assert find_reinforced(ia)["double_whammies"] == []


def test_find_reinforced_focal_point():
    ia = [{"a": "A.Sun", "type": "conjunction", "b": "B.Venus", "orb": 1.0},
          {"a": "A.Mars", "type": "square", "b": "B.Venus", "orb": 2.0},
          {"a": "A.Saturn", "type": "trine", "b": "B.Venus", "orb": 3.0}]
    r = find_reinforced(ia)
    bvenus = [f for f in r["focal_points"] if f["body"] == "B.Venus"]
    assert bvenus and bvenus[0]["count"] == 3


def test_build_synastry_data_has_reinforced():
    sd = build_synastry_data(BIRTH_A, BIRTH_B)
    assert isinstance(sd["double_whammies"], list)
    assert isinstance(sd["focal_points"], list)


def _stdin_payload(monkeypatch):
    payload = json.dumps({"birth_a": BIRTH_A, "birth_b": BIRTH_B, "relationship_type": "romantic"})
    monkeypatch.setattr(sys, "stdin", io.StringIO(payload))


def test_cli_default_prints_to_stdout_without_writing(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _stdin_payload(monkeypatch)
    rc = main([])
    assert rc == 0
    assert "# Synastry" in capsys.readouterr().out
    assert list(tmp_path.iterdir()) == []  # no synastry.md left in the working tree


def test_cli_out_writes_file(tmp_path, monkeypatch, capsys):
    dest = tmp_path / "synastry.md"
    _stdin_payload(monkeypatch)
    rc = main(["--out", str(dest)])
    assert rc == 0
    assert "# Synastry" in dest.read_text(encoding="utf-8")
    assert "Keep birth data private" in capsys.readouterr().out
