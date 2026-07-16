"""Tests for mbti_score.py — synthetic charts with hand-computed expectations,
plus ABC/UNK e2e pinned from the 2026-07-15 prototype gate."""
import json

import pytest

import mbti_score as ms


def make_cd(signs=None, houses=None, asc="Aries", aspects=()):
    """Minimal chart-data dict in build_chart_data's shape. signs/houses:
    dict body→value; unlisted planets default to Aries / house 5 for outers,
    house 6 for the rest (6 is EI/SN-neutral for a single body)."""
    order = ["Sun", "Moon", "Mercury", "Venus", "Mars",
             "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
    planets = []
    for b in order:
        planets.append({"body": b, "sign": (signs or {}).get(b, "Aries"),
                        "degree": 0.0,
                        "house": (houses or {}).get(b, 5 if b in ("Uranus", "Neptune", "Pluto") else 6),
                        "retrograde": False})
    return {"planets": planets,
            "angles": {"ASC": {"sign": asc, "degree": 0.0}},
            "aspects": [{"a": a, "type": t, "b": b, "orb": 1.0} for a, t, b in aspects]}


ALL_FIRE = {b: "Aries" for b in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn")}
FIRE_HOUSES = {"Sun": 10, "Moon": 7, "Mercury": 7, "Venus": 10, "Mars": 1}
ALL_EARTH = {b: "Virgo" for b in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn")}
EARTH_HOUSES = {"Sun": 2, "Moon": 3, "Mercury": 6, "Venus": 3, "Mars": 6}


def test_all_fire_cardinal_chart_is_high_confidence_ENFJ():
    cd = make_cd(ALL_FIRE, FIRE_HOUSES, asc="Aries")
    res = ms.score_chart(cd)
    ei, sn, tf, jp = (res["axes"][a] for a in ("EI", "SN", "TF", "JP"))
    # votes 9.0 E + angular cap 2.0 + above-horizon 1.0 + Sun-house 1.0 = 13.0
    assert (ei["net"], ei["max"], ei["letter"], ei["confidence"]) == (13.0, 13.0, "E", "high")
    # fire→N full votes 9.0; no 9/12 emphasis
    assert (sn["net"], sn["max"], sn["letter"], sn["confidence"]) == (9.0, 11.5, "N", "high")
    # fire→F half votes 4.5 + Moon/Venus angular F-group cap 1.5 → net -6.0
    assert (tf["net"], tf["max"], tf["letter"], tf["confidence"]) == (-6.0, 12.0, "F", "high")
    # cardinal full votes 9.0
    assert (jp["net"], jp["max"], jp["letter"], jp["confidence"]) == (9.0, 11.5, "J", "high")
    assert res["type"] == "ENFJ"


def test_all_earth_mutable_chart_is_ISTP():
    cd = make_cd(ALL_EARTH, EARTH_HOUSES, asc="Virgo")
    res = ms.score_chart(cd)
    ei, sn, tf, jp = (res["axes"][a] for a in ("EI", "SN", "TF", "JP"))
    # earth→I 9.0 + below-horizon 1.0 + Sun in house 2 → 1.0 = 11.0 I
    assert (ei["net"], ei["letter"], ei["confidence"]) == (-11.0, "I", "high")
    # earth→S 9.0 + 3rd/6th emphasis 1.0
    assert (sn["net"], sn["letter"]) == (-10.0, "S")
    # earth→T half votes 4.5, no F-group hits
    assert (tf["net"], tf["letter"], tf["confidence"]) == (4.5, "T", "medium")
    assert (jp["net"], jp["letter"]) == (-9.0, "P")
    assert res["type"] == "ISTP"


def test_factor_lists_name_the_contributors():
    cd = make_cd(ALL_FIRE, FIRE_HOUSES, asc="Aries")
    res = ms.score_chart(cd)
    ei_factors = [f["factor"] for f in res["axes"]["EI"]["factors"]]
    assert "Sun in Aries (fire)" in ei_factors
    assert "angular personal planets: Sun, Moon, Mercury, Venus, Mars" in ei_factors
    assert "above-horizon majority (4/5)" in ei_factors
    assert "Sun in house 10" in ei_factors
    ang = next(f for f in res["axes"]["EI"]["factors"] if f["factor"].startswith("angular"))
    assert ang["weight"] == 2.0  # 5 × 0.5 capped at 2.0


def test_aspect_factors_with_caps_and_sextile_excluded():
    aspects = [("Uranus", "square", "Sun"), ("Neptune", "trine", "Mercury"),
               ("Saturn", "conjunction", "Sun"), ("Saturn", "square", "Moon"),
               ("Saturn", "opposition", "Mercury"), ("Jupiter", "square", "Moon"),
               ("Neptune", "opposition", "Sun"), ("Uranus", "sextile", "Moon")]
    cd = make_cd(ALL_EARTH, EARTH_HOUSES, asc="Virgo", aspects=aspects)
    res = ms.score_chart(cd)
    # SN: 3 Uranus/Neptune hits (sextile ignored), capped → +1.5 N; votes -10.0 → -8.5
    assert res["axes"]["SN"]["net"] == -8.5
    # TF: 3 Saturn hits → capped 1.5 T; votes +4.5 → +6.0
    assert res["axes"]["TF"]["net"] == 6.0
    sat = next(f for f in res["axes"]["TF"]["factors"]
               if f["factor"].startswith("Saturn major aspect"))
    assert sat["weight"] == 1.5
    # JP: Saturn→luminaries binary +1.0 J; Jupiter□Moon + Neptune☍Sun → 1.5 P
    # votes -9.0 → -9.0 + 1.0 - 1.5 = -9.5
    assert res["axes"]["JP"]["net"] == -9.5
    assert not any("sextile" in f["factor"] for f in res["axes"]["SN"]["factors"])


def test_single_aspect_hit_scores_the_unit_below_cap():
    cd = make_cd(ALL_EARTH, EARTH_HOUSES, asc="Virgo",
                 aspects=[("Uranus", "square", "Sun")])
    res = ms.score_chart(cd)
    un = next(f for f in res["axes"]["SN"]["factors"]
              if f["factor"].startswith("Uranus/Neptune major aspect"))
    assert un["weight"] == 0.75  # one hit × ASPECT_UNIT, below the 1.5 cap
    assert res["axes"]["SN"]["net"] == -9.25  # votes -10.0 + 0.75 N


def test_fgroup_shared_cap_across_angular_and_aspects():
    aspects = [("Moon", "trine", "Mercury"), ("Venus", "conjunction", "Mercury")]
    cd = make_cd(ALL_FIRE, FIRE_HOUSES, asc="Aries", aspects=aspects)
    res = ms.score_chart(cd)
    fg = next(f for f in res["axes"]["TF"]["factors"]
              if f["factor"].startswith("Moon/Venus emphasis"))
    # 2 angular (Moon h7, Venus h10) + 2 Mercury aspects = 4 hits → capped 1.5
    assert fg["weight"] == 1.5
    assert "Moon angular (house 7)" in fg["factor"]
    assert "Moon trine Mercury" in fg["factor"]


def _axes_stub(nets_maxes):
    return {a: {"factors": [], "net": n, "max": m}
            for a, (n, m) in nets_maxes.items()}


def test_exact_tie_flagged_and_letter_deterministic():
    v = ms._verdicts(_axes_stub({"EI": (0.0, 10.0), "SN": (5.0, 10.0),
                                 "TF": (5.0, 10.0), "JP": (5.0, 10.0)}), True)
    assert v["axes"]["EI"]["exact_tie"] is True
    assert v["axes"]["EI"]["near_tie"] is True
    assert v["axes"]["EI"]["letter"] == "E"   # deterministic positive-side letter
    assert v["type"] == "ENTJ" and v["runner_up"] == "INTJ"


def test_runner_up_flips_smallest_ratio_near_tie_axis():
    # ABC's pinned nets/maxima: SN ratio 0.087, TF ratio 0.042 → TF flips
    v = ms._verdicts(_axes_stub({"EI": (2.0, 13.0), "SN": (1.0, 11.5),
                                 "TF": (0.5, 12.0), "JP": (6.5, 11.5)}), True)
    assert v["near_tie_axes"] == ["TF", "SN"]
    assert v["type"] == "ENTJ" and v["runner_up"] == "ENFJ"


def test_no_near_ties_means_no_runner_up():
    v = ms._verdicts(_axes_stub({"EI": (13.0, 13.0), "SN": (9.0, 11.5),
                                 "TF": (-6.0, 12.0), "JP": (9.0, 11.5)}), True)
    assert v["runner_up"] is None and v["near_tie_axes"] == []


def test_unknown_time_caps_EI_JP_confidence():
    v = ms._verdicts(_axes_stub({"EI": (6.0, 7.5), "SN": (3.0, 9.0),
                                 "TF": (1.0, 10.5), "JP": (2.5, 10.0)}), False)
    assert v["axes"]["EI"]["confidence"] == "low" and v["axes"]["EI"]["capped"] is True
    assert v["axes"]["JP"]["confidence"] == "low" and v["axes"]["JP"]["capped"] is True
    assert v["axes"]["SN"]["confidence"] == "medium" and v["axes"]["SN"]["capped"] is False


def test_unknown_time_drops_asc_and_house_factors():
    cd = make_cd(ALL_FIRE, FIRE_HOUSES, asc="Aries")
    res = ms.score_chart(cd, time_known=False)
    ei = res["axes"]["EI"]
    assert (ei["net"], ei["max"]) == (7.5, 7.5)      # votes only, no ASC
    assert ei["confidence"] == "low" and ei["capped"] is True
    labels = " | ".join(f["factor"] for a in res["axes"].values() for f in a["factors"])
    for banned in ("ASC", "angular", "horizon", "house"):
        assert banned not in labels
    assert (res["axes"]["SN"]["max"], res["axes"]["TF"]["max"],
            res["axes"]["JP"]["max"]) == (9.0, 10.5, 10.0)


def test_moon_dropped_removes_votes_and_aspect_participation():
    aspects = [("Saturn", "conjunction", "Moon")]
    cd = make_cd(ALL_FIRE, FIRE_HOUSES, asc="Aries", aspects=aspects)
    res = ms.score_chart(cd, time_known=False, moon_ok=False)
    assert res["axes"]["EI"]["max"] == 6.0            # 7.5 - Moon 1.5
    labels = " | ".join(f["factor"] for a in res["axes"].values() for f in a["factors"])
    assert "Moon" not in labels                       # no votes, no Saturn→Moon T factor


def test_moon_sign_check_uses_day_boundaries():
    calls = []

    def fake_build(birth):
        calls.append((birth["hour"], birth["minute"]))
        sign = "Virgo" if birth["hour"] == 0 else "Libra"
        return make_cd({"Moon": sign})

    stable, s0, s1 = ms.moon_sign_check(fake_build, {"hour": 9, "minute": 9})
    assert (stable, s0, s1) == (False, "Virgo", "Libra")
    assert calls == [(0, 0), (23, 59)]

    stable, s0, s1 = ms.moon_sign_check(lambda b: make_cd({"Moon": "Virgo"}),
                                        {"hour": 9, "minute": 9})
    assert (stable, s0, s1) == (True, "Virgo", "Virgo")


META_OK = """# Birth Data

## Meta
- name: ABC
- date: 2000-01-01
- time: 12:00
- location: London
- lat: 51.5074
- lon: -0.1278
- tz: Europe/London
- house_system: Placidus
- language: en

## Planets
- Sun: sign=Capricorn degree=10.5 house=10 retrograde=no
"""


def test_read_birth_meta_parses_meta_block_only(tmp_path):
    p = tmp_path / "birth-data.md"
    p.write_text(META_OK, encoding="utf-8")
    m = ms.read_birth_meta(str(p))
    assert m == {"name": "ABC", "date": "2000-01-01", "time": "12:00",
                 "lat": 51.5074, "lon": -0.1278, "tz": "Europe/London",
                 "house_system": "Placidus", "language": "en"}


def test_read_birth_meta_unknown_time(tmp_path):
    p = tmp_path / "birth-data.md"
    p.write_text(META_OK.replace("- time: 12:00", "- time: unknown"), encoding="utf-8")
    assert ms.read_birth_meta(str(p))["time"] is None


def test_read_birth_meta_missing_fields(tmp_path):
    p = tmp_path / "birth-data.md"
    p.write_text(META_OK.replace("- tz: Europe/London\n", ""), encoding="utf-8")
    with pytest.raises(ValueError, match="missing Meta field.*tz"):
        ms.read_birth_meta(str(p))


def test_read_birth_meta_strips_template_comments(tmp_path):
    # birth-data.template.md ships inline comments on Meta lines; editing a
    # value in place must not carry the comment into the parsed value.
    p = tmp_path / "birth-data.md"
    contaminated = META_OK.replace(
        "- language: en",
        "- language: zh     <!-- en or zh; this is your DEFAULT output language -->",
    ).replace("- time: 12:00", "- time: 12:00  <!-- HH:MM, 24h -->")
    p.write_text(contaminated, encoding="utf-8")
    m = ms.read_birth_meta(str(p))
    assert m["language"] == "zh" and m["time"] == "12:00"


def test_read_birth_meta_unfilled_template_gives_missing_fields(tmp_path):
    p = tmp_path / "birth-data.md"
    p.write_text("""# Birth Data

## Meta
- name:  <!-- optional -->
- date:  <!-- YYYY-MM-DD -->
- time:  <!-- HH:MM, 24h -->
- lat: <!-- signed decimal degrees -->
- lon: <!-- signed decimal degrees -->
- tz: <!-- e.g. Asia/Shanghai or +08:00 -->
""", encoding="utf-8")
    with pytest.raises(ValueError, match="missing Meta field"):
        ms.read_birth_meta(str(p))


def test_read_birth_meta_stops_after_first_meta_block(tmp_path):
    p = tmp_path / "birth-data.md"
    p.write_text(META_OK + """
## Meta
- name: Impostor
- tz: America/New_York
""", encoding="utf-8")
    m = ms.read_birth_meta(str(p))
    assert m["name"] == "ABC" and m["tz"] == "Europe/London"


DISC_EN = ("This is a folklore game, not a measurement. Astrology→MBTI has no "
           "scientific correlation; if this feels accurate, research says that's "
           "self-attribution, not the stars. For your real type, take an actual "
           "MBTI instrument.")
DISC_ZH = ("这是民俗游戏，不是测量。占星→MBTI 没有科学相关性；如果觉得准，研究表明那是"
           "自我归因，不是星星。想知道真实类型，请做正式的 MBTI 测试。")


def _full_res(lang="en", time_known=True):
    cd = make_cd(ALL_FIRE, FIRE_HOUSES, asc="Aries")
    res = ms.score_chart(cd, time_known=time_known)
    res["meta"] = {"name": "ABC", "date": "2000-01-01",
                   "time": "12:00" if time_known else None,
                   "time_known": time_known, "lang": lang}
    res["degraded"] = None if time_known else {
        "time_unknown": True, "dropped": ["ASC votes", "angular/hemisphere/house factors"],
        "moon": {"stable": True, "sign_0000": "Aries", "sign_2359": "Aries", "dropped": False}}
    res["disclaimer"] = ms.DISCLAIMER[lang]
    return res


def test_disclaimers_are_canonical_verbatim():
    assert ms.DISCLAIMER["en"] == DISC_EN
    assert ms.DISCLAIMER["zh"] == DISC_ZH


def test_markdown_order_axes_then_type_then_disclaimer_then_footnote():
    md = ms.render_markdown(_full_res("en"), "en")
    i_axes = md.index("## Axes (primary content)")
    i_type = md.index("## Your type — for fun only")
    i_disc = md.index(DISC_EN)
    i_foot = md.index("Lineage:")
    assert i_axes < i_type < i_disc < i_foot
    assert "**ENFJ**" in md


def test_markdown_zh_canonical_strings():
    md = ms.render_markdown(_full_res("zh"), "zh")
    assert "## 逐轴倾向（主体）" in md
    assert "## 你的类型——仅供娱乐" in md
    assert DISC_ZH in md and "谱系：" in md


def test_markdown_degradation_notice_present():
    md = ms.render_markdown(_full_res("en", time_known=False), "en")
    assert "## Degradation notice" in md
    assert "Birth time unknown — computed at 12:00" in md
    assert "capped" in md


def test_markdown_exact_tie_shows_both_letters():
    res = _full_res("en")
    res["axes"]["EI"].update({"exact_tie": True, "net": 0.0, "ratio": 0.0})
    md = ms.render_markdown(res, "en")
    assert "E/I (exact 50/50)" in md


def test_markdown_zh_order_and_moon_dropped_notice():
    res = _full_res("zh", time_known=False)
    res["degraded"]["moon"] = {"stable": False, "sign_0000": "Virgo",
                               "sign_2359": "Libra", "dropped": True}
    md = ms.render_markdown(res, "zh")
    assert "当日月亮换座（Virgo → Libra）；月亮因子已剔除。" in md
    i_axes = md.index("## 逐轴倾向（主体）")
    i_type = md.index("## 你的类型——仅供娱乐")
    i_disc = md.index(DISC_ZH)
    i_foot = md.index("谱系：")
    assert i_axes < i_type < i_disc < i_foot


ABC_ARGS = ["--date", "2000-01-01", "--time", "12:00", "--lat", "51.5074",
            "--lon", "-0.1278", "--tz", "Europe/London", "--name", "ABC"]
UNK_ARGS = ["--date", "1988-11-05", "--time-unknown", "--lat", "-33.87",
            "--lon", "151.21", "--tz", "Australia/Sydney", "--name", "UNK"]


def test_load_chart_backend_missing_natal(tmp_path):
    with pytest.raises(RuntimeError, match="requires the natal-astrology skill"):
        ms.load_chart_backend(natal_dir=str(tmp_path))


def test_cli_argument_errors(capsys):
    assert ms.main(["--birth-data", "x.md", "--date", "2000-01-01"]) == 1
    assert "not both" in capsys.readouterr().err
    assert ms.main(["--date", "2000-01-01", "--lat", "1", "--lon", "1",
                    "--tz", "UTC", "--time", "12:00", "--time-unknown"]) == 1
    assert "mutually exclusive" in capsys.readouterr().err
    assert ms.main(["--date", "2000-01-01", "--lat", "1", "--lon", "1", "--tz", "UTC"]) == 1
    assert "--time HH:MM or --time-unknown" in capsys.readouterr().err
    assert ms.main(["--time", "12:00", "--lat", "1", "--lon", "1", "--tz", "UTC"]) == 1
    assert "--date" in capsys.readouterr().err
    assert ms.main(ABC_ARGS[:-2] + ["--date", "bad-date"]) == 1  # malformed date → error path


def test_abc_e2e_matches_prototype_gate(capsys):
    assert ms.main(ABC_ARGS + ["--json"]) == 0
    res = json.loads(capsys.readouterr().out)
    assert res["type"] == "ENTJ" and res["runner_up"] == "ENFJ"
    assert res["near_tie_axes"] == ["TF", "SN"]
    expect = {"EI": (2.0, 13.0, "E", "low"), "SN": (1.0, 11.5, "N", "low"),
              "TF": (0.5, 12.0, "T", "low"), "JP": (6.5, 11.5, "J", "high")}
    for axis, (net, mx, letter, conf) in expect.items():
        a = res["axes"][axis]
        assert (a["net"], a["max"], a["letter"], a["confidence"]) == (net, mx, letter, conf)
    assert res["degraded"] is None


def test_unk_e2e_degraded_matches_prototype_gate(capsys):
    assert ms.main(UNK_ARGS + ["--json"]) == 0
    res = json.loads(capsys.readouterr().out)
    assert res["type"] == "ENTJ" and res["runner_up"] == "INTJ"
    assert res["near_tie_axes"] == ["EI"]
    assert [res["axes"][a]["max"] for a in ("EI", "SN", "TF", "JP")] == [7.5, 9.0, 10.5, 10.0]
    assert res["axes"]["JP"]["net"] == 2.5
    assert res["axes"]["JP"]["confidence"] == "low" and res["axes"]["JP"]["capped"] is True
    assert res["degraded"]["moon"] == {"stable": True, "sign_0000": "Virgo",
                                       "sign_2359": "Virgo", "dropped": False}


def test_determinism_two_runs_identical(capsys):
    assert ms.main(ABC_ARGS) == 0
    out1 = capsys.readouterr().out
    assert ms.main(ABC_ARGS) == 0
    assert capsys.readouterr().out == out1
    assert DISC_EN in out1 and "**ENTJ**" in out1
