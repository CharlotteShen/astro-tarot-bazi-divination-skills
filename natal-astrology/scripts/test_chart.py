import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
pytest.importorskip("kerykeion")

from chart import build_chart_data, render_markdown  # noqa: E402

BIRTH = {
    "name": "Test",
    "year": 1990, "month": 6, "day": 15, "hour": 12, "minute": 0,
    "lat": 31.23, "lon": 121.47, "tz": "Asia/Shanghai",
    "city": "Shanghai", "house_system": "Placidus",
}

PLANET_NAMES = {"Sun", "Moon", "Mercury", "Venus", "Mars",
                "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"}


def test_subject_helper_builds():
    from chart import _subject
    subj = _subject(BIRTH)
    assert hasattr(subj, "sun") and subj.sun.sign


def test_house_code_rejects_unknown():
    from chart import _house_code
    import pytest as _pytest
    with _pytest.raises(ValueError):
        _house_code(dict(BIRTH, house_system="Regiomontanus"))


def test_has_ten_planets():
    cd = build_chart_data(BIRTH)
    names = {p["body"] for p in cd["planets"]}
    assert names == PLANET_NAMES


def test_each_planet_well_formed():
    cd = build_chart_data(BIRTH)
    for p in cd["planets"]:
        assert 0 <= p["degree"] < 30
        assert 1 <= p["house"] <= 12
        assert isinstance(p["retrograde"], bool)
        assert p["sign"]


def test_angles_present():
    cd = build_chart_data(BIRTH)
    assert cd["angles"]["ASC"]["sign"]
    assert cd["angles"]["MC"]["sign"]


def test_aspects_reference_known_bodies():
    cd = build_chart_data(BIRTH)
    known = PLANET_NAMES | {"North Node", "Chiron", "ASC", "MC"}
    assert cd["aspects"]  # non-empty
    for a in cd["aspects"]:
        assert a["a"] in known and a["b"] in known
        assert a["type"] in {"conjunction", "sextile", "square", "trine", "opposition"}
        assert a["orb"] <= 10


def test_balance_sums_to_ten():
    cd = build_chart_data(BIRTH)
    assert sum(cd["balance"]["elements"].values()) == 10
    assert sum(cd["balance"]["modalities"].values()) == 10


def test_render_markdown_roundtrips_planets():
    cd = build_chart_data(BIRTH)
    md = render_markdown(cd)
    for name in PLANET_NAMES:
        assert name in md
    assert "## Planets" in md and "## Angles" in md and "## Aspects" in md


def test_unsupported_house_system_raises():
    bad = dict(BIRTH, house_system="Regiomontanus")
    with pytest.raises(ValueError):
        build_chart_data(bad)


SIGNS_SET = {"Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
             "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"}


def _abs(point):  # reconstruct absolute longitude from a {sign,degree} dict
    order = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
             "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    return order.index(point["sign"]) * 30 + point["degree"]


def _enr():
    return build_chart_data(BIRTH)["enrichment"]


def test_enrichment_block_keys():
    e = _enr()
    assert set(e) == {"sect", "lots", "midpoints", "declinations", "parallels", "vertex",
                       "asteroids", "black_moon_lilith", "asteroid_contacts"}
    assert e["sect"] in ("day", "night")
    assert set(e["lots"]) == {"fortune", "spirit", "eros"}


def test_sect_noon_is_day():
    # BIRTH is 12:00 — Sun near the MC, above the horizon → day chart
    assert _enr()["sect"] == "day"


def test_fortune_spirit_mirror_asc():
    # Spirit is the reflection of Fortune across the Ascendant: Fortune + Spirit ≡ 2·ASC (mod 360)
    cd = build_chart_data(BIRTH)
    asc = _abs(cd["angles"]["ASC"])
    f, s = _abs(cd["enrichment"]["lots"]["fortune"]), _abs(cd["enrichment"]["lots"]["spirit"])
    expected, got = (2 * asc) % 360, (f + s) % 360
    assert min(abs(got - expected), 360 - abs(got - expected)) < 0.5


def test_sun_moon_midpoint():
    cd = build_chart_data(BIRTH)
    pos = {p["body"]: _abs(p) for p in cd["planets"]}
    a, b = pos["Sun"], pos["Moon"]
    diff = ((b - a + 540) % 360) - 180
    mid = (a + diff / 2) % 360
    got = _abs(cd["enrichment"]["midpoints"]["sun_moon"])
    assert min(abs(mid - got), 360 - abs(mid - got)) < 0.1


def test_declinations_planets():
    decl = _enr()["declinations"]
    for p in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
              "Uranus", "Neptune", "Pluto"):
        assert -30 <= decl[p] <= 30


def test_vertex_valid():
    v = _enr()["vertex"]
    assert v["sign"] in SIGNS_SET and 1 <= v["house"] <= 12
    assert isinstance(_enr()["parallels"], list)


def test_asteroids_block_keys():
    e = _enr()
    assert set(e["asteroids"]) == {"ceres", "pallas", "juno", "vesta"}
    assert e["black_moon_lilith"] is not None
    assert isinstance(e["asteroid_contacts"], list)


def test_asteroids_well_formed():
    e = _enr()
    for b in list(e["asteroids"].values()) + [e["black_moon_lilith"]]:
        assert b["sign"] in SIGNS_SET
        assert 0 <= b["degree"] < 30
        assert 1 <= b["house"] <= 12


def test_asteroid_contacts_well_formed():
    from chart import ASTEROID_ORB
    e = _enr()
    body_names = {"Ceres", "Pallas", "Juno", "Vesta", "Black Moon Lilith"}
    targets = PLANET_NAMES | {"ASC", "MC"}
    for c in e["asteroid_contacts"]:
        assert c["a"] in body_names
        assert c["b"] in targets
        assert c["type"] in {"conjunction", "sextile", "square", "trine", "opposition"}
        assert c["orb"] <= ASTEROID_ORB


def test_asteroid_positions_deterministic():
    a1 = build_chart_data(BIRTH)["enrichment"]["asteroids"]["ceres"]
    a2 = build_chart_data(BIRTH)["enrichment"]["asteroids"]["ceres"]
    assert a1 == a2
