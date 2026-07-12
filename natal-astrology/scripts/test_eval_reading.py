import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from eval_reading import grade, main  # noqa: E402

EXPECT = {
    "reading_type": "natal",
    "must_mention": [
        {"desc": "Sun trine Saturn", "patterns": [r"(?i)sun[^.]{0,80}trine[^.]{0,80}saturn",
                                                   r"(?i)saturn[^.]{0,80}trine[^.]{0,80}sun",
                                                   "太阳[^。]{0,60}土星[^。]{0,30}三分"]},
        {"desc": "Capricorn Sun", "patterns": [r"(?i)capricorn", "摩羯"]},
    ],
    "forbidden": [
        {"desc": "fabricated: Sun trine Moon", "patterns": [r"(?i)sun[^.]{0,60}trine[^.]{0,60}moon"]},
    ],
    "must_flag": [
        {"desc": "unknown-time caveat", "patterns": [r"(?i)birth time[^.]{0,80}unknown", "出生时间未知"]},
    ],
}

GOOD = ("Your Capricorn Sun forms a trine to Saturn, grounding your ambition. "
        "Note: your birth time is unknown, so houses are unreliable.")
MISSING = "Your Capricorn Sun is steady. Note: your birth time is unknown."
FABRICATED = ("Your Capricorn Sun trine Saturn is steady, and your Sun makes a trine to your Moon. "
              "Note: your birth time is unknown.")
ZH = "你的摩羯太阳与土星形成三分相。出生时间未知，宫位不可靠。"


def test_all_pass():
    r = grade(EXPECT, GOOD)
    assert r["passed"] is True
    assert all(item["ok"] for item in r["results"])
    assert r["counts"]["failed"] == 0


def test_missing_must_mention_fails():
    r = grade(EXPECT, MISSING)
    assert r["passed"] is False
    bad = [i for i in r["results"] if not i["ok"]]
    assert len(bad) == 1 and bad[0]["kind"] == "must_mention" and "Saturn" in bad[0]["desc"]


def test_forbidden_fails():
    r = grade(EXPECT, FABRICATED)
    assert r["passed"] is False
    bad = [i for i in r["results"] if not i["ok"]]
    assert any(i["kind"] == "forbidden" for i in bad)


def test_any_of_patterns_chinese():
    r = grade(EXPECT, ZH)
    assert r["passed"] is True   # zh patterns satisfy both must_mention items and the flag


def test_cli_pass_and_fail(tmp_path, capsys):
    import json
    e = tmp_path / "e.json"
    e.write_text(json.dumps(EXPECT), encoding="utf-8")
    good = tmp_path / "good.md"
    good.write_text(GOOD, encoding="utf-8")
    bad = tmp_path / "bad.md"
    bad.write_text(MISSING, encoding="utf-8")
    assert main(["--expect", str(e), "--reading", str(good)]) == 0
    out = capsys.readouterr().out
    assert "PASS" in out
    assert main(["--expect", str(e), "--reading", str(bad)]) == 1


def test_cli_missing_file_errors(capsys):
    rc = main(["--expect", "/nonexistent/e.json", "--reading", "/nonexistent/r.md"])
    assert rc == 1
    assert "Error" in capsys.readouterr().err


def test_shipped_natal_known_expect_wellformed():
    import json
    path = os.path.join(os.path.dirname(__file__), "..", "evals", "fixtures",
                        "natal-known.expect.json")
    with open(path, encoding="utf-8") as f:
        expect = json.load(f)
    snippet = ("Your Capricorn Sun sits right on the Midheaven — the Sun conjunct MC is the loudest "
               "signal here, and the Sun's trine to Saturn steadies it. Jupiter conjunct your Aries "
               "rising broadens how you meet the world, while your Scorpio Moon runs deep.")
    r = grade(expect, snippet)
    assert r["passed"] is True
