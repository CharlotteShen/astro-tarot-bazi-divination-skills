import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..",
                                "natal-astrology", "scripts"))

from draw import draw_spread  # noqa: E402
from make_expect import BARNUM, SALIENT, build_expect, load_zh_names, main  # noqa: E402
from eval_reading import grade  # noqa: E402

FIXDIR = os.path.join(os.path.dirname(__file__), "..", "evals", "fixtures")


def test_zh_names_cover_deck():
    zh = load_zh_names()
    assert len(zh) == 78
    assert zh["The Magician"] == "魔术师"
    assert zh["Ten of Wands"] == "权杖十"
    assert zh["The Star"] == "星星"


def test_skeleton_covers_seed15_draw():
    exp = build_expect({"reading_type": "tarot", "spread": "three", "seed": 15})
    assert exp["reading_type"] == "tarot" and exp["must_flag"] == []
    all_must = " ".join(p for item in exp["must_mention"] for p in item["patterns"])
    for c in draw_spread("three", 15):
        assert c["card"].lower() in all_must     # an EN pattern per drawn card
    assert sum(1 for i in exp["must_mention"]
               if i["desc"].startswith("reversal read")) == 1   # only The Magician is reversed
    assert any(i["desc"].startswith("seed") for i in exp["must_mention"])
    assert "15" in all_must


def test_string_seed_coerced_to_int():
    # a quoted "15" must not silently seed the RNG from the string hash (a different draw)
    assert build_expect({"spread": "three", "seed": "15"}) == \
        build_expect({"spread": "three", "seed": 15})


def test_forbidden_skips_drawn_salient_and_keeps_three():
    # seed 2 draws Wheel of Fortune — a salient major must never decoy its own draw
    drawn = {c["card"] for c in draw_spread("three", 2)}
    assert "Wheel of Fortune" in drawn          # guard: the premise of this test
    exp = build_expect({"spread": "three", "seed": 2})
    fabricated = [i for i in exp["forbidden"] if i["desc"].startswith("fabricated")]
    assert len(fabricated) == 3
    assert not any("wheel of fortune" in i["desc"].lower() for i in fabricated)


def test_no_forbidden_pattern_matches_ground_truth():
    exp = build_expect({"spread": "three", "seed": 15})
    zh = load_zh_names()
    synthetic = "; ".join(f"{c['position']}: {c['card']} ({c['orientation']}) {zh[c['card']]}"
                          for c in draw_spread("three", 15)) + " seed: 15"
    for item in exp["forbidden"]:
        for pat in item["patterns"]:
            assert not re.search(pat, synthetic), f"{item['desc']} matched the draw itself"


def test_salient_list_is_collision_safe():
    # common-word majors can appear in grounded prose — they must never be fabrication decoys
    for banned in ("Death", "Strength", "Justice", "The Sun", "The Moon", "The Star"):
        assert banned not in SALIENT


def test_cli_emits_parseable_json(capsys, tmp_path):
    fixture = tmp_path / "f.json"
    fixture.write_text(json.dumps({"spread": "three", "seed": 15}), encoding="utf-8")
    rc = main(["--fixture", str(fixture)])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert set(data) == {"reading_type", "must_mention", "forbidden", "must_flag"}


def test_cli_missing_fixture_errors(capsys):
    rc = main(["--fixture", "nope.json"])
    assert rc == 1
    assert "Error" in capsys.readouterr().err


def _fixture_names():
    return sorted(f[:-5] for f in os.listdir(FIXDIR)
                  if f.endswith(".json") and not f.endswith(".expect.json"))


def test_committed_fixture_pairs_exist():
    names = _fixture_names()
    assert names == ["three-en", "three-zh"]
    for n in names:
        assert os.path.exists(os.path.join(FIXDIR, f"{n}.expect.json"))


def test_committed_expects_match_pinned_draws():
    """The determinism payoff: re-draw each pinned seed and hold the committed expectations to it.
    Guards hand-tuning drift and any future spread/deck edits."""
    zh = load_zh_names()
    for name in _fixture_names():
        with open(os.path.join(FIXDIR, f"{name}.json"), encoding="utf-8") as f:
            fx = json.load(f)
        with open(os.path.join(FIXDIR, f"{name}.expect.json"), encoding="utf-8") as f:
            exp = json.load(f)
        cards = draw_spread(fx["spread"], fx["seed"])
        all_must = " ".join(p for item in exp["must_mention"] for p in item["patterns"])
        for c in cards:   # (a) every drawn card covered by a must_mention pattern
            assert c["card"].lower() in all_must.lower() or zh[c["card"]] in all_must, \
                f"{name}: {c['card']} not covered by must_mention"
        assert str(fx["seed"]) in all_must   # (c) seed digits present
        synthetic = "; ".join(f"{c['position']}: {c['card']} ({c['orientation']}) {zh[c['card']]}"
                              for c in cards) + f" seed: {fx['seed']} 种子{fx['seed']}"
        for item in exp["forbidden"]:   # (b) no forbidden pattern hits the ground-truth draw
            for pat in item["patterns"]:
                assert not re.search(pat, synthetic), f"{name}: {item['desc']} matched the draw"


COMPLIANT_EN = """# Three-Card — seed: 15
Question: How should ABC approach the new work collaboration?
Past — Five of Wands (upright): the project so far has been a scramble of competing ideas,
five voices sketching on one whiteboard; friction, but creative friction.
Present — The Magician (reversed): your skill is real, but the energy is blocked and turned
inward — you are rehearsing instead of showing your hand.
Future — Three of Pentacles (upright): craft made visible and valued; the collaboration works
when each contribution is on the table.
Next step: draft the one-page role-scope note tonight and send it to the team before Friday.
"""


def test_grade_compliant_reading_passes():
    with open(os.path.join(FIXDIR, "three-en.expect.json"), encoding="utf-8") as f:
        exp = json.load(f)
    result = grade(exp, COMPLIANT_EN)
    assert result["passed"], [r for r in result["results"] if not r["ok"]]


COMPLIANT_ZH = """# 三牌阵 — seed: 22
问题：ABC 未来一年的职业方向应该往哪里走？
过去 — 星星（正位）：一段修复与重燃希望的时期，你重新确认了自己真正想走的专业方向。
现在 — 权杖十（逆位）：担子全压在你一个人肩上，能量向内堵住——有两件事本不该由你来扛。
未来 — 女皇（正位）：把想法慢慢养育成形，让作品替你说话。
下一步：本周五之前列出你目前的全部职责，选出其中两项移交或砍掉。
"""


def test_grade_compliant_zh_reading_passes():
    # exercises the 中文 patterns against realistic prose (the EN sample can't reach them)
    with open(os.path.join(FIXDIR, "three-zh.expect.json"), encoding="utf-8") as f:
        exp = json.load(f)
    result = grade(exp, COMPLIANT_ZH)
    assert result["passed"], [r for r in result["results"] if not r["ok"]]


def test_barnum_ignores_disclaimer_quotation_but_catches_assertion():
    # Mirrors bazi's test_redline_ignores_disclaimer_enumeration_but_catches_assertion.
    with open(os.path.join(FIXDIR, "three-en.expect.json"), encoding="utf-8") as f:
        exp = json.load(f)
    # committed fixture Barnum items stay identical to the generator list — guard both from drift
    assert [i for i in exp["forbidden"] if i["desc"].startswith("Barnum")] == BARNUM
    # naming the banned advice to REFUSE it (distant negation) or QUOTE it must not trip forbidden
    disclaimed = (COMPLIANT_EN
                  + "\nI will not tell you to just trust your intuition or that it will all work out."
                  + "\nThis is not a stay balanced, communicate more kind of reading.")
    result = grade(exp, disclaimed)
    assert result["passed"], [r for r in result["results"] if not r["ok"]]
    # but a genuine Barnum assertion is still caught — exactly its one item
    asserted = COMPLIANT_EN + "\nHonestly, just trust your intuition."
    result2 = grade(exp, asserted)
    bad = [r for r in result2["results"] if not r["ok"]]
    assert len(bad) == 1 and bad[0]["desc"] == "Barnum: trust your intuition"
