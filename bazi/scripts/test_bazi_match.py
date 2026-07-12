import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from bazi_match import (LIUCHONG, LIUHAI, LIUHE, SANHE, WUHE, XIANGPO, ZIXING,  # noqa: E402
                        build_match, gan_relation, main, shishen, zhi_relations)

A = ["--a-year", "2000", "--a-month", "1", "--a-day", "1", "--a-hour", "12", "--a-minute", "0",
     "--a-lon", "-0.1278", "--a-lat", "51.5074", "--a-tz", "Europe/London", "--a-gender", "女"]
B = ["--b-year", "1995", "--b-month", "6", "--b-day", "15", "--b-hour", "8", "--b-minute", "30",
     "--b-lon", "2.35", "--b-lat", "48.85", "--b-tz", "Europe/Paris", "--b-gender", "男"]

ABC = {"year": 2000, "month": 1, "day": 1, "hour": 12, "minute": 0,
       "lon": -0.1278, "lat": 51.5074, "tz": "Europe/London", "gender": "女"}
XYZ = {"year": 1995, "month": 6, "day": 15, "hour": 8, "minute": 30,
       "lon": 2.35, "lat": 48.85, "tz": "Europe/Paris", "gender": "男"}


def match(**over):
    args = {"a": dict(ABC), "b": dict(XYZ), "date": "2026-07-01", "true_solar": True}
    args.update(over)
    return build_match(args)


def test_tables_exhaustive():
    assert len(LIUHE) == len(LIUCHONG) == len(LIUHAI) == len(XIANGPO) == 6
    assert len(WUHE) == 5
    assert set("".join(sorted("".join(p) for p in (tuple(x) for x in WUHE)))) == set("甲乙丙丁戊己庚辛壬癸")
    assert ZIXING == set("辰午酉亥")
    trios = list(SANHE.values())
    assert all(len(t) == 3 for t in trios)
    assert len(set("".join(trios))) == 12          # 十二支全覆盖、互不重叠


def test_gan_relation_directions():
    assert gan_relation("戊", "癸") == "五合化火"
    assert gan_relation("戊", "丁") == "B生A"
    assert gan_relation("丁", "戊") == "A生B"
    assert gan_relation("丙", "壬") == "B克A"       # 壬水克丙火
    assert gan_relation("甲", "甲") == "同气"


def test_shishen_mutual():
    assert shishen("戊", "丁") == "正印"           # 丁是戊的正印
    assert shishen("丁", "戊") == "伤官"           # 戊是丁的伤官


def test_zhi_relations_pairs():
    assert "六合" in zhi_relations("子", "丑")
    assert "六冲" in zhi_relations("子", "午")
    assert "相害" in zhi_relations("丑", "午")
    assert "自刑" in zhi_relations("午", "午")
    assert any(t.startswith("半合") and "木" in t for t in zhi_relations("卯", "亥"))
    assert "相破" in zhi_relations("午", "卯")
    both = zhi_relations("寅", "亥")               # 六合与相破共存——多标签如实全列
    assert "六合" in both and "相破" in both
    assert any("半合" in t for t in zhi_relations("子", "辰"))   # 子辰半合水
    assert "相刑" in zhi_relations("子", "卯")      # 子卯无礼之刑


def test_overview_constants():
    m = match()
    a, b = m["甲方"], m["乙方"]
    assert a["四柱"] == "己卯 丙子 戊午 戊午" and a["日主"] == "戊"
    assert b["四柱"] == "乙亥 壬午 丁丑 癸卯" and b["日主"] == "丁"
    assert a["当前大运"] == "己卯（2021–2030）" and b["当前大运"] == "己卯（2018–2027）"


def test_day_pillar_verdict():
    m = match()
    d = m["日柱判定"]
    assert d["判定"] == "天干相生、地支相害"
    assert d["日干关系"] == "B生A"
    assert d["互为十神"] == {"乙方日干之于甲方": "正印", "甲方日干之于乙方": "伤官"}


def test_wuhe_hits_two_positions():
    m = match()
    hits = [e for e in m["天干互动"] if e["关系"] == "五合化火" and e["干"] == "戊×癸"]
    assert len(hits) == 2                          # 甲日干×乙时干、甲时干×乙时干


def test_zhi_matrix_hits():
    m = match()
    tagged = {(e["位置"], t) for e in m["地支互动"] for t in e["关系"]}
    tags = {t for _, t in tagged}
    assert "六合" in tags and "六冲" in tags and "相害" in tags and "自刑" in tags and "相破" in tags
    assert any(t.startswith("半合") for t in tags)
    assert ("甲方月支×乙方月支", "六冲") in tagged   # 子午冲在月×月


def test_spouse_star_raw():
    m = match()
    sa, sb = m["夫妻星"]["甲方"], m["夫妻星"]["乙方"]
    assert sa["配偶星"] == "官杀" and sa["透干位"] == [] and sa["藏支位"] == ["年"] \
        and sa["坐支逢空"] is False
    assert sb["配偶星"] == "财星" and sb["透干位"] == [] and sb["藏支位"] == ["日"] \
        and sb["坐支逢空"] is False


def test_dayun_sync():
    m = match()
    s = m["大运同频"]
    assert s["甲方"]["当前"] == "己卯（2021–2030）" and s["甲方"]["下一步"] == "庚辰（2031–2040）"
    assert s["乙方"]["当前"] == "己卯（2018–2027）" and s["乙方"]["下一步"] == "戊寅（2028–2037）"
    assert s["当前同干支"] is True


def test_unknown_hour_side_degrades():
    m = match(a={**ABC, "hour": "unknown"})
    assert len(m["甲方"]["四柱"].split()) == 3      # 三柱
    assert not any("甲方时" in e["位置"] for e in m["天干互动"])
    assert any("时辰不明" in n for n in m["标注"])


def test_json_cli_schema_and_labels(capsys):
    rc = main(A + B + ["--date", "2026-07-01", "--json"])
    assert rc == 0
    d = json.loads(capsys.readouterr().out)
    assert set(d) >= {"甲方", "乙方", "天干互动", "地支互动", "日柱判定", "夫妻星",
                      "大运同频", "参考日期", "标注"}
    rc = main(A + B + ["--date", "2026-07-01", "--a-label", "小甲", "--b-label", "小乙"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "小甲" in out and "小乙" in out and "戊×癸" in out and "午×丑" in out


def test_cli_bad_tz_errors(capsys):
    bad = list(A)
    bad[bad.index("Europe/London")] = "Not/AZone"
    rc = main(bad + B)
    assert rc == 1
    assert "Error" in capsys.readouterr().err
