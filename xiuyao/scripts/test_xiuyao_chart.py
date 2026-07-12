"""宿曜排宿测试——常量全部来自 2026-07-09 门禁记录（勿改）。"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from xiuyao_chart import (
    CYCLE, ANCHOR, GROUPS, LIUHAI_OFFSETS,
    benming_xiu, relation, liuhai_name, main,
)

PY = sys.executable
SCRIPT = str(Path(__file__).parent / "xiuyao_chart.py")


# ---------- 常量表 ----------

def test_cycle_27_no_niu():
    assert len(CYCLE) == 27
    assert len(set(CYCLE)) == 27
    assert "牛" not in CYCLE
    assert CYCLE[0] == "昴" and CYCLE[-1] == "胃"

def test_anchor_table():
    assert ANCHOR == {1: "室", 2: "奎", 3: "胃", 4: "毕", 5: "参", 6: "鬼",
                      7: "张", 8: "角", 9: "氐", 10: "心", 11: "斗", 12: "虚"}
    assert all(x in CYCLE for x in ANCHOR.values())

def test_groups_partition():
    all_x = [x for xs in GROUPS.values() for x in xs]
    assert sorted(all_x) == sorted(CYCLE)
    assert len(GROUPS["北方玄武"]) == 6  # 无牛

# ---------- 本命宿 ----------

def test_ground_truth_senjutsu():
    r = benming_xiu(1986, 10, 19)
    assert r["宿"] == "毕"
    assert "九月" in r["农历"] and "十六" in r["农历"]

def test_fixtures():
    assert benming_xiu(2000, 1, 1)["宿"] == "心"    # ABC
    assert benming_xiu(1995, 6, 15)["宿"] == "虚"   # XYZ
    assert benming_xiu(1988, 11, 5)["宿"] == "角"   # UNK

def test_celebrity_cross_checks():
    assert benming_xiu(1981, 1, 28)["宿"] == "心"   # 星野源（rensa 心宿名单）
    assert benming_xiu(1986, 3, 28)["宿"] == "心"   # Lady Gaga

def test_leap_month():
    r = benming_xiu(2023, 3, 25)  # 闰二月初四：奎锚 +3 → 昴
    assert r["闰月"] is True
    assert "闰" in r["农历"]
    assert r["宿"] == "昴"

def test_group_lookup():
    assert benming_xiu(2000, 1, 1)["四象组"] == "东方青龙"  # 心

# ---------- 三九相性 ----------

def test_relation_ming_ye_tai():
    assert relation("心", "心") == {"关系": "命", "距离": None}
    assert relation("昴", "翼") == {"关系": "业", "距离": None}
    assert relation("昴", "斗") == {"关系": "胎", "距离": None}
    assert relation("虚", "角") == {"关系": "胎", "距离": None}
    assert relation("角", "虚") == {"关系": "业", "距离": None}

def test_relation_full_row_bou():
    # 八雲院昴宿整行（门禁 52/52 之前 26 项）
    expect = {"毕": ("荣", "近"), "女": ("荣", "中"), "轸": ("荣", "远"),
              "胃": ("亲", "近"), "张": ("亲", "中"), "箕": ("亲", "远"),
              "娄": ("友", "近"), "星": ("友", "中"), "尾": ("友", "远"),
              "觜": ("衰", "近"), "虚": ("衰", "中"), "角": ("衰", "远"),
              "参": ("安", "近"), "危": ("安", "中"), "亢": ("安", "远"),
              "奎": ("坏", "近"), "柳": ("坏", "中"), "心": ("坏", "远"),
              "井": ("危", "近"), "室": ("危", "中"), "氐": ("危", "远"),
              "壁": ("成", "近"), "鬼": ("成", "中"), "房": ("成", "远"),
              "翼": ("业", None), "斗": ("胎", None)}
    for other, (rel, dist) in expect.items():
        got = relation("昴", other)
        assert (got["关系"], got["距离"]) == (rel, dist), other

def test_relation_xin_xu_pinned():
    assert relation("心", "虚") == {"关系": "成", "距离": "中"}
    assert relation("虚", "心") == {"关系": "危", "距离": "中"}

def test_relation_reciprocity_all():
    pair = {"荣": "亲", "亲": "荣", "衰": "友", "友": "衰", "安": "坏",
            "坏": "安", "危": "成", "成": "危", "业": "胎", "胎": "业", "命": "命"}
    for a in CYCLE:
        for b in CYCLE:
            ab, ba = relation(a, b), relation(b, a)
            assert ba["关系"] == pair[ab["关系"]], (a, b)
            assert ab["距离"] == ba["距离"], (a, b)

# ---------- 六害 ----------

def test_liuhai_offsets():
    assert LIUHAI_OFFSETS == {0: "命", 3: "意", 9: "事", 12: "克", 15: "聚", 19: "同"}

def test_liuhai_from_bou():
    # 昴的六害位：昴(命) 参(意) 翼(事) 亢(克) 心(聚) 女(同)
    assert liuhai_name("昴", "昴") == "命"
    assert liuhai_name("昴", "参") == "意"
    assert liuhai_name("昴", "翼") == "事"
    assert liuhai_name("昴", "亢") == "克"
    assert liuhai_name("昴", "心") == "聚"
    assert liuhai_name("昴", "女") == "同"
    assert liuhai_name("昴", "毕") is None

# ---------- CLI ----------

def run_cli(*args):
    return subprocess.run([PY, SCRIPT, *args], capture_output=True, text=True)

def test_cli_single_text():
    r = run_cli("--year", "2000", "--month", "1", "--day", "1",
                "--date", "2026-07-09")
    assert r.returncode == 0
    for token in ["心宿", "东方青龙", "冬月", "值日宿", "昴宿", "克", "标注"]:
        assert token in r.stdout, token

def test_cli_single_json():
    r = run_cli("--year", "2000", "--month", "1", "--day", "1",
                "--date", "2026-07-09", "--json")
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert set(out) == {"甲方", "日运", "标注", "参考日期"}
    assert out["甲方"]["宿"] == "心"
    assert "乙方" not in out["日运"]
    assert out["日运"]["值日宿"] == "昴"
    assert out["日运"]["甲方"]["关系"] == {"关系": "安", "距离": "远"}
    assert out["日运"]["甲方"]["六害位"] == "克"

def test_cli_pair_json():
    r = run_cli("--year", "2000", "--month", "1", "--day", "1",
                "--b-year", "1995", "--b-month", "6", "--b-day", "15",
                "--date", "2026-07-09", "--json")
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert set(out) == {"甲方", "乙方", "相性", "日运", "标注", "参考日期"}
    assert out["甲方"]["宿"] == "心" and out["乙方"]["宿"] == "虚"
    assert out["相性"]["甲方看乙方"] == {"关系": "成", "距离": "中"}
    assert out["相性"]["乙方看甲方"] == {"关系": "危", "距离": "中"}
    assert out["日运"]["值日宿"] == "昴"
    assert out["日运"]["甲方"]["六害位"] == "克"

def test_cli_labels():
    r = run_cli("--year", "2000", "--month", "1", "--day", "1",
                "--b-year", "1995", "--b-month", "6", "--b-day", "15",
                "--label", "小明", "--b-label", "小红", "--date", "2026-07-09")
    assert "小明" in r.stdout and "小红" in r.stdout

def test_cli_errors():
    r = run_cli("--year", "2000", "--month", "13", "--day", "1")
    assert r.returncode != 0 and "错误" in r.stderr
    # lunar-python 对 2 月 31 日会静默滚动到 3 月——脚本必须自己校验拒绝
    r2 = run_cli("--year", "2000", "--month", "2", "--day", "31")
    assert r2.returncode != 0 and "错误" in r2.stderr
    r3 = run_cli("--year", "2000", "--month", "1", "--day", "1",
                 "--b-year", "1995")  # 残缺 --b-*
    assert r3.returncode != 0 and "错误" in r3.stderr
