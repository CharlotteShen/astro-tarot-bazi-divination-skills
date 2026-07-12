import io
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
pytest.importorskip("kerykeion")

from davison import build_davison, build_marks, davison_birth, main  # noqa: E402

BIRTH_A = {"name": "A", "year": 1990, "month": 3, "day": 15, "hour": 14, "minute": 30,
           "lat": 39.90, "lon": 116.41, "tz": "Asia/Shanghai", "city": "Beijing",
           "house_system": "Placidus"}
BIRTH_B = {"name": "B", "year": 1988, "month": 11, "day": 5, "hour": 18, "minute": 45,
           "lat": 31.23, "lon": 121.47, "tz": "Asia/Shanghai", "city": "Shanghai",
           "house_system": "Placidus"}

PLANETS = {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
           "Uranus", "Neptune", "Pluto"}
MAJORS = {"conjunction", "sextile", "square", "trine", "opposition"}


def test_davison_birth_midpoint_utc_and_place():
    a = {"name": "A", "year": 2000, "month": 1, "day": 1, "hour": 0, "minute": 0,
         "lat": 0.0, "lon": 0.0, "tz": "UTC", "house_system": "Placidus"}
    b = {"name": "B", "year": 2000, "month": 1, "day": 3, "hour": 0, "minute": 0,
         "lat": 40.0, "lon": 20.0, "tz": "UTC", "house_system": "Placidus"}
    db = davison_birth(a, b)
    assert (db["year"], db["month"], db["day"], db["hour"], db["minute"]) == (2000, 1, 2, 0, 0)
    assert db["lat"] == 20.0 and db["lon"] == 10.0 and db["tz"] == "UTC"


def test_davison_chart_shape():
    d = build_davison(BIRTH_A, BIRTH_B)
    assert {p["body"] for p in d["planets"]} == PLANETS
    assert d["angles"]["ASC"]["sign"] and d["angles"]["MC"]["sign"]
    assert len(d["cusps"]) == 12
    assert d["aspects"]
    for x in d["aspects"]:
        assert x["type"] in MAJORS and x["orb"] <= 8


def test_marks_default_is_natal_davison():
    m = build_marks(BIRTH_A, BIRTH_B)
    assert m["mode"] == "natal_davison"
    for side in ("a", "b"):
        assert m[side]["inter_aspects"] and len(m[side]["overlays"]) == 10
        for x in m[side]["inter_aspects"]:
            assert x["a"].startswith("N.") and x["b"].startswith("R.") and x["type"] in MAJORS
        for o in m[side]["overlays"]:
            assert 1 <= o["house"] <= 12


def test_marks_natal_composite():
    m = build_marks(BIRTH_A, BIRTH_B, "natal_composite")
    assert m["mode"] == "natal_composite"
    assert m["a"]["inter_aspects"] and len(m["b"]["overlays"]) == 10


def test_marks_canonical_charts():
    m = build_marks(BIRTH_A, BIRTH_B, "canonical")
    assert m["mode"] == "canonical"
    for side in ("a", "b"):
        assert {p["body"] for p in m[side]["planets"]} == PLANETS
        assert m[side]["angles"]["ASC"]["sign"] and m[side]["angles"]["MC"]["sign"]


def test_unknown_mode_raises():
    with pytest.raises(ValueError):
        build_marks(BIRTH_A, BIRTH_B, "bogus")


def test_marks_canonical_meta_complete():
    m = build_marks(BIRTH_A, BIRTH_B, "canonical")
    for side in ("a", "b"):
        meta = m[side]["meta"]
        assert meta["datetime_utc"].endswith("Z")
        assert "lat" in meta and "lon" in meta
        assert "davison(davison" in meta["source"]


def _stdin_payload(monkeypatch, target="davison"):
    payload = json.dumps({"birth_a": BIRTH_A, "birth_b": BIRTH_B, "target": target})
    monkeypatch.setattr(sys, "stdin", io.StringIO(payload))


def test_cli_default_prints_json_to_stdout_without_writing(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _stdin_payload(monkeypatch)
    rc = main([])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert {p["body"] for p in data["planets"]} == PLANETS
    assert list(tmp_path.iterdir()) == []  # no relationship.json left in the working tree


def test_cli_out_writes_file(tmp_path, monkeypatch, capsys):
    dest = tmp_path / "relationship.json"
    _stdin_payload(monkeypatch)
    rc = main(["--out", str(dest)])
    assert rc == 0
    data = json.loads(dest.read_text(encoding="utf-8"))
    assert {p["body"] for p in data["planets"]} == PLANETS
    assert "Keep birth data private" in capsys.readouterr().out
