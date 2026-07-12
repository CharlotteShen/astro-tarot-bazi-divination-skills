import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))

from ziwei_chart import build_chart, main  # noqa: E402

ABC = {"year": 2000, "month": 1, "day": 1, "hour": 12, "minute": 0,
       "lon": -0.1278, "lat": 51.5074, "tz": "Europe/London", "gender": "女"}


def chart(**over):
    a = dict(ABC)
    a.update(over)
    return build_chart(a)


def _palace(c, name):
    return next(p for p in c["十二宫"] if p["宫名"] == name)


def test_abc_basics():
    c = chart(date="2026-07-01")
    b = c["基本"]
    assert b["命主"] == "破军" and b["身主"] == "天同"
    assert b["五行局"] == "土五局"
    assert "冬月廿五" in b["农历"]
    assert "午时" in b["时辰"]


def test_abc_ming_palace_ziwei():
    c = chart(date="2026-07-01")
    ming = _palace(c, "命宫")
    assert ming["干支"] == "庚午"
    assert ming["大限"] == "5–14"
    names = [s["名"] for s in ming["主星"]]
    assert "紫微" in names
    ziwei = next(s for s in ming["主星"] if s["名"] == "紫微")
    assert ziwei["亮度"] == "庙"


def test_birth_year_sihua_ji_gan():
    # 己干四化：武曲禄、贪狼权、天梁科、文曲忌（文曲在辅星）——经典十干四化表
    c = chart(date="2026-07-01")
    got = {}
    for p in c["十二宫"]:
        for s in p["主星"] + p["辅星"]:
            if s["生年四化"]:
                got[s["名"]] = s["生年四化"]
    assert got == {"武曲": "禄", "贪狼": "权", "天梁": "科", "文曲": "忌"}


def test_tianfu_in_guanlu_jiaxu():
    c = chart(date="2026-07-01")
    guanlu = _palace(c, "官禄宫")
    assert guanlu["干支"] == "甲戌"
    assert "天府" in [s["名"] for s in guanlu["主星"]]


def test_current_scopes_2026():
    c = chart(date="2026-07-01")
    da = c["大限"]
    assert da["宫位"] == "福德宫" and da["干支"] == "壬申" and da["起讫岁"] == "25–34"
    assert da["四化(禄权科忌)"] == ["天梁", "紫微", "左辅", "武曲"]
    ln = c["流年"]
    assert ln["宫位"] == "命宫" and ln["干支"] == "丙午"
    assert ln["四化(禄权科忌)"] == ["天同", "天机", "文昌", "廉贞"]
    lm = c["流月"]
    assert lm["干支"] == "甲午"
    assert lm["四化(禄权科忌)"] == ["廉贞", "破军", "武曲", "太阳"]


UNTRANSLATED = re.compile(r"[A-Za-z]+(Maj|Min|Heavenly|Earthly|Palace)")


def test_no_untranslated_keys_anywhere():
    c = chart(date="2026-07-01")
    dump = json.dumps(c, ensure_ascii=False)
    m = UNTRANSLATED.search(dump)
    assert not m, f"未翻译的内部 key 泄漏: {m.group(0) if m else ''}"


def test_true_solar_boundary_flips_hour_branch():
    # 伦敦夏令时（bazi 已验证值）：2000-07-01 12:00 钟表时 → 真太阳时 10:55，午时→巳时
    on = chart(month=7, day=1, date="2026-07-01")
    assert "巳时" in on["基本"]["时辰"]
    assert any("改变了时辰" in n for n in on["标注"])
    off = chart(month=7, day=1, true_solar=False, date="2026-07-01")
    assert "午时" in off["基本"]["时辰"]


def test_late_zi_keeps_same_lunar_day():
    # 引擎实测：23 时晚子时不换日（与八字主流派一致）——钉死该行为
    c = chart(hour=23, minute=30, true_solar=False, date="2026-07-01")
    assert "冬月廿五" in c["基本"]["农历"]
    assert "子时" in c["基本"]["时辰"]
    # 子时生 → 命宫=生月宫=子宫（安星诀手推验证；早前原型误读 palaces[4] 为命宫）
    assert _palace(c, "命宫")["干支"] == "丙子"


def test_leap_month_fix_leap_pinned():
    # 2004 闰二月十六：fix_leap=True（默认）的整盘结构钉死；False 整盘移位（引擎实测）
    c = build_chart({"year": 2004, "month": 4, "day": 5, "hour": 12, "minute": 0,
                     "lon": 120.0, "lat": 30.0, "tz": "Asia/Shanghai", "gender": "男",
                     "true_solar": False, "date": "2026-07-01"})
    assert "闰二月" in c["基本"]["农历"]
    # 该盘紫微在午 → 命宫（戌）坐廉贞+天府（紫微系结构手推验证）；fix_leap=False 则整盘移位
    assert [s["名"] for s in _palace(c, "命宫")["主星"]] == ["廉贞", "天府"]


def test_hour_unknown_errors():
    try:
        chart(hour="unknown")
        raise AssertionError("should have raised")
    except ValueError as e:
        assert "时辰" in str(e)


def test_json_cli_and_schema(capsys):
    rc = main(["--year", "2000", "--month", "1", "--day", "1", "--hour", "12",
               "--minute", "0", "--lon", "-0.1278", "--lat", "51.5074",
               "--tz", "Europe/London", "--gender", "女",
               "--date", "2026-07-01", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert set(data) >= {"基本", "时间处理", "十二宫", "大限", "流年", "流月", "标注"}
    assert len(data["十二宫"]) == 12
    assert sum(1 for p in data["十二宫"] if p["身宫"]) == 1


def test_cli_text_output_shows_key_facts(capsys):
    rc = main(["--year", "2000", "--month", "1", "--day", "1", "--hour", "12",
               "--minute", "0", "--lon", "-0.1278", "--lat", "51.5074",
               "--tz", "Europe/London", "--gender", "女", "--date", "2026-07-01"])
    assert rc == 0
    out = capsys.readouterr().out
    for token in ("紫微", "命宫", "庚午", "福德宫", "丙午", "土五局", "禄权科忌"):
        assert token in out


def test_cli_unknown_hour_errors(capsys):
    rc = main(["--year", "2000", "--month", "1", "--day", "1", "--hour", "unknown",
               "--lon", "0", "--tz", "Asia/Shanghai", "--gender", "女"])
    assert rc == 1
    assert "Error" in capsys.readouterr().err
