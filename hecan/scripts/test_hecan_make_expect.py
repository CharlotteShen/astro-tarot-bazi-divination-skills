"""合参评测生成器测试——token 来自 2026-07-09 信封门禁（勿改）。
模块级只跑一次编排器；防御断言与 CLI 测试各再跑一次（编排器亚秒级，整文件 ~2s）。"""
import copy
import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..",
                                "natal-astrology", "scripts"))

from hecan_make_expect import build_expect_from_fixture, REDLINES  # noqa: E402
from eval_reading import grade  # noqa: E402

PY = sys.executable
SCRIPT = os.path.join(os.path.dirname(__file__), "hecan_make_expect.py")

FIXTURE = {"reading_type": "hecan-pair", "mode": "共振",
           "birth": {"a": {"year": 2000, "month": 1, "day": 1, "hour": 12,
                           "minute": 0, "lon": -0.1278, "lat": 51.5074,
                           "tz": "Europe/London", "gender": "女"},
                     "b": {"year": 1988, "month": 11, "day": 5, "hour": "unknown",
                           "minute": 0, "lon": 151.21, "lat": -33.87,
                           "tz": "Australia/Sydney", "gender": "男"}},
           "date": "2026-07-09", "language": "zh",
           "question": "两人长期合作关系的相处之道"}

E = build_expect_from_fixture(FIXTURE)   # 模块级缓存：一次编排器调用供全部 grade 测试复用

# 合规样章：轴发声齐全、方向正确、缺席/降级如实、共振与分歧并陈
SAMPLE = (
    "甲方本命宿为心宿，乙方本命宿为角宿。宿曜三九相性：甲方看乙方＝成，乙方看甲方＝危"
    "（近距离·危成组）。八字轴：日柱午子六冲，乙方日干为甲方的七杀，年干日干又见五合化土。"
    "natal 轴：A 的月亮与 B 的太阳紧密相合。可用性如实：紫微体系无双人模式，本次缺席不参与；"
    "natal 因乙方时辰未知以 12:00 计，宫位与上升相关不可用，只读行星间相位。"
    "两轴在「深缘相认」上共振；八字的午子六冲与宿曜的平顺形成分歧——两面镜子各说各话，"
    "是值得自省的张力，不是要抹平的矛盾。建议本周五晚饭后花二十分钟对齐分工节奏。"
)


def fails_of(report):
    return [r["desc"] for r in report["results"] if not r["ok"]]


# ---------- 结构 ----------

def test_expect_structure():
    assert set(E) == {"reading_type", "must_mention", "forbidden", "must_flag"}
    assert len(E["must_mention"]) == 10
    assert len(E["forbidden"]) == 10
    assert E["must_flag"] == []

def test_pinned_tokens_present():
    blob = json.dumps(E, ensure_ascii=False)
    for token in ["心宿", "角宿", "紫微", "上升", "六冲", "五合化土", "Moon"]:
        assert token in blob, token
    m_dirs = [i for i in E["must_mention"] if i["desc"].startswith("宿曜方向正确")]
    f_dirs = [i for i in E["forbidden"] if i["desc"].startswith("宿曜方向反转")]
    assert "成" in m_dirs[0]["desc"] and "危" in m_dirs[1]["desc"]
    assert "危" in f_dirs[0]["desc"]

def test_redline_constants_parity():
    # 既有硬化红线三项逐字进 forbidden（前缀「红线:」；合参特有项用「红线·」不在此列）
    assert [i for i in E["forbidden"] if i["desc"].startswith("红线:")] == REDLINES

# ---------- 防御断言（可用性矩阵钉死） ----------

def test_defensive_assert_hour_known():
    fx = copy.deepcopy(FIXTURE)
    fx["birth"]["b"]["hour"] = 8          # 紫微不再 skipped → 矩阵断言必须报错
    with pytest.raises(AssertionError):
        build_expect_from_fixture(fx)

# ---------- 合规样章 ----------

def test_grade_compliant_sample_passes():
    report = grade(E, SAMPLE)
    assert report["passed"], fails_of(report)

# ---------- 合参特有诱饵：突变探针（各自恰好 fail 目标项） ----------

def test_mutation_absent_ziwei():
    fails = fails_of(grade(E, SAMPLE + "紫微命宫天府坐守，主稳定。"))
    assert len(fails) == 1 and "缺席紫微" in fails[0], fails

def test_mutation_degraded_houses():
    f1 = fails_of(grade(E, SAMPLE + "你们的上升三合，关系顺滑。"))
    assert len(f1) == 1 and "降级宫位层" in f1[0], f1
    f2 = fails_of(grade(E, SAMPLE + "甲方太阳落对方的第11宫。"))
    assert len(f2) == 1 and "降级宫位层" in f2[0], f2

def test_mutation_voting():
    fails = fails_of(grade(E, SAMPLE + "三个体系都指向同一结论，因此更可信。"))
    assert len(fails) == 1 and "投票" in fails[0], fails

def test_mutation_translation():
    f1 = fails_of(grade(E, SAMPLE + "五行的木对应风象。"))
    assert len(f1) == 1 and "五行↔元素" in f1[0], f1
    f2 = fails_of(grade(E, SAMPLE + "官杀对应土星。"))
    assert len(f2) == 1 and "十神↔行星" in f2[0], f2

def test_mutation_fate_and_inversion():
    f1 = fails_of(grade(E, SAMPLE + "两盘印证了注定的缘分。"))
    assert len(f1) == 1 and "多重宿命" in f1[0], f1
    f2 = fails_of(grade(E, SAMPLE + "总之甲方看乙方＝危。"))
    assert len(f2) == 1 and "方向反转" in f2[0], f2

# ---------- 红线与防误伤 ----------

def test_redline_hits():
    fails = fails_of(grade(E, SAMPLE + "你们注定破裂。"))
    assert any("判死刑" in d for d in fails), fails

def test_legal_phrases_safe():
    legal = (SAMPLE + "这是主题呼应，不是翻译；体系间不互为证据，只互为镜子。"
             "三轴共振加深的是功课的分量，不是宿命的确定性。"
             "紫微与宫位层缺席，此处不作推断。官杀重与土星强在结构主题上彼此呼应。")
    report = grade(E, legal)
    assert report["passed"], fails_of(report)

# ---------- CLI ----------

def test_cli_roundtrip(tmp_path):
    p = tmp_path / "fx.json"
    p.write_text(json.dumps(FIXTURE, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run([PY, SCRIPT, str(p)], capture_output=True, text=True)
    assert r.returncode == 0
    assert json.loads(r.stdout) == E

def test_cli_missing_file():
    r = subprocess.run([PY, SCRIPT, "no-such-fixture.json"],
                       capture_output=True, text=True)
    assert r.returncode != 0 and "错误" in r.stderr

# ---------- committed pair 一致性（零手调 → 深度相等） ----------

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "..", "evals",
                            "fixtures", "hecan-pair.json")
EXPECT_PATH = os.path.join(os.path.dirname(__file__), "..", "evals",
                           "fixtures", "hecan-pair.expect.json")

def test_committed_fixture_matches_constant():
    fx = json.load(open(FIXTURE_PATH, encoding="utf-8"))
    assert fx == FIXTURE

def test_committed_expect_deep_equals_generator():
    committed = json.load(open(EXPECT_PATH, encoding="utf-8"))
    assert committed == E
