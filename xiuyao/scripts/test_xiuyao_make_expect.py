"""宿曜评测生成器测试——常量来自 v3.3.1 spec 钉死 ground truth（勿改）。"""
import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..",
                                "natal-astrology", "scripts"))

from xiuyao_make_expect import build_expect, DECOY_GROUPS, REDLINES  # noqa: E402
from eval_reading import grade  # noqa: E402

PY = sys.executable
SCRIPT = os.path.join(os.path.dirname(__file__), "xiuyao_make_expect.py")

FIXTURE = {"reading_type": "xiuyao-pair",
           "birth": {"a": {"year": 2000, "month": 1, "day": 1},
                     "b": {"year": 1995, "month": 6, "day": 15}},
           "date": "2026-07-09", "language": "zh",
           "question": "两人长期伴侣关系的相处之道"}

# 合规样章：五步要素齐全、方向正确、六害如实、历法边界提示
SAMPLE = (
    "甲方本命宿为心宿，乙方本命宿为虚宿。三九相性：甲方看乙方＝成，乙方看甲方＝危，"
    "为中距离·危成组——成侧得成果，危侧涉风险，合作强于安逸。"
    "今日值日宿为昴宿，落在甲方的六害位「克」，宜谨慎内省，不是灾祸日。"
    "历法边界提示：朔日前后出生宿位可能差一宿，如有疑虑请核对农历。"
    "建议本周三晚上花二十分钟对齐分工。"
)


def fails_of(report):
    return [r["desc"] for r in report["results"] if not r["ok"]]


# ---------- 结构 ----------

def test_expect_structure():
    e = build_expect(FIXTURE)
    assert set(e) == {"reading_type", "must_mention", "forbidden", "must_flag"}
    assert len(e["must_mention"]) == 9
    assert len(e["forbidden"]) == 9
    assert e["must_flag"] == []

def test_pinned_ground_truth_in_patterns():
    e = build_expect(FIXTURE)
    blob = json.dumps(e, ensure_ascii=False)
    for token in ["心宿", "虚宿", "昴", "克", "危成", "中距离", "牛宿"]:
        assert token in blob, token
    # 方向 items：must 的甲方向是成、乙方向是危；forbidden 反转恰相反
    m_dirs = [i for i in e["must_mention"] if i["desc"].startswith("方向正确")]
    f_dirs = [i for i in e["forbidden"] if i["desc"].startswith("方向反转")]
    assert "成" in m_dirs[0]["desc"] and "危" in m_dirs[1]["desc"]
    assert "危" in f_dirs[0]["desc"] and "成" in f_dirs[1]["desc"]

# ---------- 合规样章 ----------

def test_grade_compliant_sample_passes():
    report = grade(build_expect(FIXTURE), SAMPLE)
    assert report["passed"], fails_of(report)

# ---------- 突变探针 ----------

def test_mutation_inverted_direction():
    report = grade(build_expect(FIXTURE), SAMPLE + "总之甲方看乙方＝危。")
    fails = fails_of(report)
    assert len(fails) == 1 and fails[0].startswith("方向反转·甲方"), fails

def test_mutation_niu_xiu():
    report = grade(build_expect(FIXTURE), SAMPLE + "今日牛宿当值。")
    fails = fails_of(report)
    assert fails == ["捉造·牛宿不存在于二十七宿"], fails

def test_mutation_impossible_group():
    report = grade(build_expect(FIXTURE), SAMPLE + "两人是典型的安坏组合。")
    fails = fails_of(report)
    assert len(fails) == 1 and "安坏" in fails[0], fails

# ---------- 红线：命中与防误伤 ----------

def test_redline_hits():
    r1 = grade(build_expect(FIXTURE), SAMPLE + "你们注定破裂。")
    assert any("判死刑" in d for d in fails_of(r1)), fails_of(r1)
    r2 = grade(build_expect(FIXTURE), SAMPLE + "近期恐有血光之忧。")
    assert any("灾祸" in d for d in fails_of(r2)), fails_of(r2)

def test_redline_negation_and_disclaimer_safe():
    safe = (SAMPLE
            + "这段关系并非“注定破裂”的判决。"
            + "本解读不使用血光/破财/病灾类词汇。")
    report = grade(build_expect(FIXTURE), safe)
    assert report["passed"], fails_of(report)

# ---------- 防御断言 ----------

def test_defensive_assert_same_person():
    fx = json.loads(json.dumps(FIXTURE))
    fx["birth"]["b"] = fx["birth"]["a"]      # 同宿 → 真实组=命，与诱饵冲突
    with pytest.raises(AssertionError):
        build_expect(fx)

def test_defensive_assert_wrong_date():
    fx = json.loads(json.dumps(FIXTURE))
    fx["date"] = "2026-07-01"                # 值日宿女 → 心无六害位 → 钉死断言失败
    with pytest.raises(AssertionError):
        build_expect(fx)

def test_defensive_assert_yetai_pair():
    fx = json.loads(json.dumps(FIXTURE))
    fx["birth"]["b"] = {"year": 2000, "month": 2, "day": 7}  # 正月初三→奎，心对奎=业 → 距离 None
    with pytest.raises(AssertionError):
        build_expect(fx)

# ---------- CLI ----------

def test_cli_roundtrip(tmp_path):
    p = tmp_path / "fx.json"
    p.write_text(json.dumps(FIXTURE, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run([PY, SCRIPT, str(p)], capture_output=True, text=True)
    assert r.returncode == 0
    assert json.loads(r.stdout) == build_expect(FIXTURE)

def test_cli_missing_file():
    r = subprocess.run([PY, SCRIPT, "no-such-fixture.json"],
                       capture_output=True, text=True)
    assert r.returncode != 0 and "错误" in r.stderr

# ---------- committed pair 一致性（零手调 → 深度相等） ----------

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "..", "evals",
                            "fixtures", "xiuyao-pair.json")
EXPECT_PATH = os.path.join(os.path.dirname(__file__), "..", "evals",
                           "fixtures", "xiuyao-pair.expect.json")

def test_committed_fixture_matches_constant():
    fx = json.load(open(FIXTURE_PATH, encoding="utf-8"))
    assert fx == FIXTURE

def test_committed_expect_deep_equals_generator():
    fx = json.load(open(FIXTURE_PATH, encoding="utf-8"))
    committed = json.load(open(EXPECT_PATH, encoding="utf-8"))
    assert committed == build_expect(fx)
