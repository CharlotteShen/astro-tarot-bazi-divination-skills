"""Tests for mbti_make_expect.py — expect generator determinism, content
sanity, defensive assertions, and end-to-end pattern validity against the
scorer's own markdown (gate-verified 2026-07-16)."""
import io
import contextlib
import json
import os
import re
import sys

import pytest

import mbti_score as ms
import mbti_make_expect as mk

FIXDIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "evals", "fixtures"))
ABC = os.path.join(FIXDIR, "abc-en.json")
UNK = os.path.join(FIXDIR, "unk-zh.json")

sys.path.insert(0, ms.NATAL_SCRIPTS)
from eval_reading import grade  # noqa: E402  (the real grader — same one the README uses)


def _build(path, followups=False):
    fx = mk.load_fixture(path)
    res, cd = mk.score_fixture(fx)
    mk.assert_ground_truth(fx, res)
    return (mk.followups_expect(fx, res) if followups
            else mk.reading_expect(fx, res, cd))


def _script_markdown(path):
    fx = mk.load_fixture(path)
    argv = ["--date", fx["date"], "--lat", str(fx["lat"]), "--lon", str(fx["lon"]),
            "--tz", fx["tz"], "--name", fx["name"], "--lang", fx["lang"]]
    argv += ["--time", fx["time"]] if fx["time"] else ["--time-unknown"]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        assert ms.main(argv) == 0
    return buf.getvalue()


def test_generator_deterministic():
    for path in (ABC, UNK):
        a = json.dumps(_build(path), sort_keys=True, ensure_ascii=False)
        b = json.dumps(_build(path), sort_keys=True, ensure_ascii=False)
        assert a == b


def test_abc_expect_sanity():
    exp = _build(ABC)
    tstr = next(i for i in exp["must_mention"] if i["desc"] == "类型串")
    assert tstr["patterns"] == [r"\bENTJ\b"]
    assert any("ENFJ" in p for i in exp["must_mention"] for p in i["patterns"])
    disc = next(i for i in exp["must_flag"] if i["desc"] == "disclaimer 逐字")
    assert disc["patterns"] == [r"\s+".join(re.escape(w)
                                            for w in ms.DISCLAIMER["en"].split())]
    sent = next(i for i in exp["forbidden"] if "哨兵" in i["desc"])
    assert "Cancer" in sent["desc"] and "Leo" in sent["desc"]


def test_unk_expect_sanity():
    exp = _build(UNK)
    descs = [i["desc"] for i in exp["must_flag"]]
    assert "降级通告" in descs and "封顶如实" in descs
    disc = next(i for i in exp["must_flag"] if i["desc"] == "disclaimer 逐字")
    assert disc["patterns"] == [r"\s+".join(re.escape(w)
                                            for w in ms.DISCLAIMER["zh"].split())]
    assert any("上升/宫位断言" in i["desc"] for i in exp["forbidden"])


def test_defensive_assertion_fires(tmp_path):
    drifted = dict(mk.load_fixture(ABC), date="1990-03-15")
    p = tmp_path / "drift.json"
    p.write_text(json.dumps(drifted), encoding="utf-8")
    fx = mk.load_fixture(str(p))
    res, _cd = mk.score_fixture(fx)
    with pytest.raises(ValueError, match="ground truth"):
        mk.assert_ground_truth(fx, res)


def test_followups_expect_tokens():
    for path, typ in ((ABC, "ENTJ"), (UNK, "ENTJ")):
        exp = _build(path, followups=True)
        mm = json.dumps(exp["must_mention"], ensure_ascii=False)
        assert "民俗游戏|folklore game" in mm
        assert any("拒手算" in i["desc"] for i in exp["must_mention"])
        fb = json.dumps(exp["forbidden"], ensure_ascii=False)
        assert typ in fb


def test_glossary_complete():
    assert len(mk.ZH_SIGN) == 12
    assert set(mk.ZH_BODY) == {"Sun", "Moon", "Mercury", "Venus", "Mars",
                               "Jupiter", "Saturn", "ASC"}


def test_patterns_match_script_output_end_to_end():
    for path in (ABC, UNK):
        verdict = grade(_build(path), _script_markdown(path))
        assert verdict["passed"], [r for r in verdict["results"] if not r["ok"]]
