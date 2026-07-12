import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..",
                                "natal-astrology", "scripts"))

from bazi_chart import build_chart  # noqa: E402
from eval_reading import grade  # noqa: E402
from bazi_make_expect import DECOY_CANDIDATES, REDLINES, build_expect, chart_tokens, main  # noqa: E402

FIXDIR = os.path.join(os.path.dirname(__file__), "..", "evals", "fixtures")

ABC_FX = {"reading_type": "bazi",
          "birth": {"year": 2000, "month": 1, "day": 1, "hour": 12, "minute": 0,
                    "lon": -0.1278, "lat": 51.5074, "tz": "Europe/London", "gender": "女"},
          "date": "2026-07-01", "language": "zh",
          "question": "ABC 未来一年的事业发展重点是什么？"}


def test_skeleton_covers_pinned_chart():
    exp = build_expect(ABC_FX)
    assert exp["reading_type"] == "bazi" and exp["must_flag"] == []
    all_must = " ".join(p for i in exp["must_mention"] for p in i["patterns"])
    for gz in ("己卯", "丙子", "戊午"):
        assert gz in all_must
    descs = " ".join(i["desc"] for i in exp["must_mention"])
    for key in ("日主戊", "身强弱", "喜用神", "当前大运己卯", "流年丙午"):
        assert key in descs


def test_decoys_screened_and_three():
    exp = build_expect(ABC_FX)
    decoys = [i["patterns"][0] for i in exp["forbidden"] if i["desc"].startswith("捉造")]
    assert len(decoys) == 3
    chart = build_chart({**ABC_FX["birth"], "date": ABC_FX["date"], "true_solar": True})
    tokens = chart_tokens(chart)
    assert not set(decoys) & tokens          # 诱饵绝不在盘面/大运/流年/流月里
    assert set(decoys) <= set(DECOY_CANDIDATES)


def test_redlines_present():
    exp = build_expect(ABC_FX)
    redline_descs = [i["desc"] for i in exp["forbidden"] if i["desc"].startswith("红线")]
    assert len(redline_descs) == 5


def test_cli_emits_parseable_json(capsys, tmp_path):
    fixture = tmp_path / "f.json"
    fixture.write_text(json.dumps(ABC_FX, ensure_ascii=False), encoding="utf-8")
    rc = main(["--fixture", str(fixture)])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert set(data) == {"reading_type", "must_mention", "forbidden", "must_flag"}


def test_cli_missing_fixture_errors(capsys):
    rc = main(["--fixture", "nope.json"])
    assert rc == 1
    assert "Error" in capsys.readouterr().err


def test_committed_fixture_pair_exists():
    assert os.path.exists(os.path.join(FIXDIR, "bazi-known.json"))
    assert os.path.exists(os.path.join(FIXDIR, "bazi-known.expect.json"))


def test_committed_expect_matches_pinned_chart():
    """确定性红利：重算钉死盘面，校验提交的期望永不漂移。"""
    with open(os.path.join(FIXDIR, "bazi-known.json"), encoding="utf-8") as f:
        fx = json.load(f)
    with open(os.path.join(FIXDIR, "bazi-known.expect.json"), encoding="utf-8") as f:
        exp = json.load(f)
    chart = build_chart({**fx["birth"], "date": fx["date"], "true_solar": True})
    all_must = " ".join(p for i in exp["must_mention"] for p in i["patterns"])
    for p in chart["四柱"].values():                          # (a) 每个柱干支被覆盖
        assert p["干支"] in all_must
    assert chart["大运"]["当前大运"]["干支"] in all_must      # (b) 当前大运
    assert chart["流年流月"]["流年"] in all_must              # (c) 流年
    tokens = chart_tokens(chart)
    for i in exp["forbidden"]:                                # (d) 诱饵仍在盘外
        if i["desc"].startswith("捉造"):
            assert i["patterns"][0] not in tokens


COMPLIANT_ZH = """# 八字解读 — ABC（示例合规片段）
四柱：己卯、丙子、戊午——日柱与时柱同为戊午。日主戊土，生于子月，月令不得令。
身强弱：虽不得令，但双午通根得地、天干比劫印星得势，两得一失——日主戊土偏强。
喜用神：身强喜克泄耗，以木为官杀疏土；原局金空缺，食伤输出是明显短板。
当前大运己卯（2021–2030），卯木正官当值；流年 2026 丙午，火印助身更旺。
建议：9 月白露前完成一次对外提交（报告或提案），把输出短板落到具体作品上。
"""


def test_compliant_zh_passes():
    with open(os.path.join(FIXDIR, "bazi-known.expect.json"), encoding="utf-8") as f:
        exp = json.load(f)
    result = grade(exp, COMPLIANT_ZH)
    assert result["passed"], [r for r in result["results"] if not r["ok"]]


def test_decoy_mutation_fails_exactly_decoy():
    with open(os.path.join(FIXDIR, "bazi-known.expect.json"), encoding="utf-8") as f:
        exp = json.load(f)
    mutated = COMPLIANT_ZH + "\n甲子大运将带来转机。"
    result = grade(exp, mutated)
    bad = [r for r in result["results"] if not r["ok"]]
    assert len(bad) == 1 and bad[0]["desc"] == "捉造: 甲子"


def test_redline_ignores_disclaimer_enumeration_but_catches_assertion():
    with open(os.path.join(FIXDIR, "bazi-known.expect.json"), encoding="utf-8") as f:
        exp = json.load(f)
    # 固定 fixture 红线与生成器 REDLINES 一致，防单边漂移。
    assert [i for i in exp["forbidden"] if i["desc"].startswith("红线")] == REDLINES
    # 免责句枚举（/ 与 、 分隔）不应误报红线——寿夭 只是被列举的禁忌主题之一。
    disclaimed = (COMPLIANT_ZH
                  + "\n本解读为传统命理视角的现代解读，不含任何医疗/法律/财务/寿夭/灾祸断言，"
                    "也不涉及生死寿夭、灾祸之说。")
    result = grade(exp, disclaimed)
    assert result["passed"], [r for r in result["results"] if not r["ok"]]
    # 但真断言式的灾祸词仍必须被抓到。
    asserted = COMPLIANT_ZH + "\n明年恐有血光之灾。"
    result2 = grade(exp, asserted)
    bad = [r for r in result2["results"] if not r["ok"]]
    assert len(bad) == 1 and bad[0]["desc"] == "红线: 血光"
