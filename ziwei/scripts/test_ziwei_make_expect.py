import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..",
                                "natal-astrology", "scripts"))

from ziwei_chart import build_chart  # noqa: E402
from eval_reading import grade  # noqa: E402
from ziwei_make_expect import (IMPOSSIBLE_SIHUA, REDLINES, build_expect,  # noqa: E402
                               layer_sihua, main)

FIXDIR = os.path.join(os.path.dirname(__file__), "..", "evals", "fixtures")

ABC_FX = {"reading_type": "ziwei",
          "birth": {"year": 2000, "month": 1, "day": 1, "hour": 12, "minute": 0,
                    "lon": -0.1278, "lat": 51.5074, "tz": "Europe/London", "gender": "女"},
          "date": "2026-07-01", "language": "zh",
          "question": "ABC 未来一年的事业发展重点是什么？"}


def test_skeleton_covers_pinned_chart():
    exp = build_expect(ABC_FX)
    assert exp["reading_type"] == "ziwei" and exp["must_flag"] == []
    descs = " ".join(i["desc"] for i in exp["must_mention"])
    for key in ("命宫主星紫微", "命身同宫", "五行局土五局", "三方四正",
                "生年四化: 武曲化禄", "生年四化: 贪狼化权", "生年四化: 天梁化科",
                "生年四化: 文曲化忌", "当前大限福德宫壬申", "流年丙午"):
        assert key in descs, key
    assert len(exp["must_mention"]) == 10


def test_impossible_decoys_and_guard():
    exp = build_expect(ABC_FX)
    decoys = [i for i in exp["forbidden"] if i["desc"].startswith("捉造")]
    assert len(decoys) == 3
    assert IMPOSSIBLE_SIHUA == ["天府", "七杀", "天相"]
    chart = build_chart({**ABC_FX["birth"], "date": ABC_FX["date"], "true_solar": True})
    legit = layer_sihua(chart)
    assert len(legit) == 16
    for star in IMPOSSIBLE_SIHUA:      # 结构性事实：三星在四层里都不四化
        assert not any(s == star for s, _ in legit), star


def test_redlines_present():
    exp = build_expect(ABC_FX)
    assert [i for i in exp["forbidden"] if i["desc"].startswith("红线")] == REDLINES


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
    assert os.path.exists(os.path.join(FIXDIR, "ziwei-known.json"))
    assert os.path.exists(os.path.join(FIXDIR, "ziwei-known.expect.json"))


def test_committed_expect_deep_equals_generator():
    """零手调 fixture：committed expect 必须与生成器输出深度相等——历代最强一致性保证。
    （将来若手调，退回 bazi 式覆盖检查并更新本测试。）"""
    with open(os.path.join(FIXDIR, "ziwei-known.json"), encoding="utf-8") as f:
        fx = json.load(f)
    with open(os.path.join(FIXDIR, "ziwei-known.expect.json"), encoding="utf-8") as f:
        exp = json.load(f)
    assert exp == build_expect(fx)


COMPLIANT_ZH = """# 紫微斗数解读 — ABC（示例合规片段）
命宫庚午坐紫微(庙)，且命身同宫——先天格局与后天着力点合一。五行局土五局，大限五岁起。
三方四正合参：命宫会迁移、财帛、官禄（甲戌天府），格局稳中带贵。
生年四化：武曲化禄利执行与财务；贪狼化权欲望与才艺要抓；天梁化科荫庇被看见；
文曲化忌是表达上的功课，不是灾祸。
当前大限行福德宫（壬申，25–34岁），大限四化再叠一层；流年 2026 丙午入命，重新定位之年。
建议：九月前把一项对外作品做完并公开发布，用文曲的功课换成果。
"""


def test_compliant_zh_passes():
    with open(os.path.join(FIXDIR, "ziwei-known.expect.json"), encoding="utf-8") as f:
        exp = json.load(f)
    result = grade(exp, COMPLIANT_ZH)
    assert result["passed"], [r for r in result["results"] if not r["ok"]]


def test_decoy_mutation_fails_exactly():
    with open(os.path.join(FIXDIR, "ziwei-known.expect.json"), encoding="utf-8") as f:
        exp = json.load(f)
    mutated = COMPLIANT_ZH + "\n明年天府化禄大旺。"
    result = grade(exp, mutated)
    bad = [r for r in result["results"] if not r["ok"]]
    assert len(bad) == 1 and bad[0]["desc"] == "捉造·不可能四化: 天府化X"


def test_non_tongong_branch_emits_body_palace_item():
    # 辰时出生 → 命宫≠身宫：生成器应改出「身宫落X宫」item（结构断言，不钉常量）
    fx = {**ABC_FX, "birth": {**ABC_FX["birth"], "hour": 8}}
    exp = build_expect(fx)
    descs = [i["desc"] for i in exp["must_mention"]]
    assert not any(d == "命身同宫" for d in descs)
    assert any(d.startswith("身宫落") for d in descs)
