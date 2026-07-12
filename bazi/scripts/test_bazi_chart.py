import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from bazi_chart import (build_chart, equation_of_time_minutes, liuyue_list,  # noqa: E402
                        main, true_solar_time)
from datetime import datetime  # noqa: E402

ABC = {"year": 2000, "month": 1, "day": 1, "hour": 12, "minute": 0,
       "lon": -0.1278, "lat": 51.5074, "tz": "Europe/London", "gender": "女"}


def chart(**over):
    a = dict(ABC)
    a.update(over)
    return build_chart(a)


def test_abc_four_pillars_raw():
    c = chart(true_solar=False, date="2026-07-01")
    assert [c["四柱"][k]["干支"] for k in ("年柱", "月柱", "日柱", "时柱")] == \
        ["己卯", "丙子", "戊午", "戊午"]
    assert c["四柱"]["日柱"]["藏干"][0] == "丁"


def test_abc_pillars_stable_under_true_solar_time():
    c = chart(true_solar=True, date="2026-07-01")
    assert [c["四柱"][k]["干支"] for k in ("年柱", "月柱", "日柱", "时柱")] == \
        ["己卯", "丙子", "戊午", "戊午"]     # 11:56 仍在午时
    t = c["时间处理"]
    assert "11:5" in t["真太阳时"]
    assert t["经度修正分钟"] < 0 and t["均时差分钟"] < 0


def test_late_zi_mainstream_keeps_day_pillar():
    c = chart(hour=23, minute=30, true_solar=False, sect="mainstream", date="2026-07-01")
    assert c["四柱"]["日柱"]["干支"] == "戊午"
    assert c["四柱"]["时柱"]["干支"] == "甲子"


def test_late_zi_traditional_advances_day_pillar():
    c = chart(hour=23, minute=30, true_solar=False, sect="traditional", date="2026-07-01")
    assert c["四柱"]["日柱"]["干支"] == "己未"
    assert c["四柱"]["时柱"]["干支"] == "甲子"


def test_early_zi_same_under_both_sects():
    for sect in ("mainstream", "traditional"):
        c = chart(hour=0, minute=30, true_solar=False, sect=sect, date="2026-07-01")
        assert c["四柱"]["日柱"]["干支"] == "戊午"
        assert c["四柱"]["时柱"]["干支"] == "壬子"


def test_dayun_start_direction_and_steps():
    c = chart(true_solar=False, date="2026-07-01")
    d = c["大运"]
    assert d["方向"] == "顺排"                      # 阴年(己)女命顺排
    assert d["起运"].startswith("1年7个月")
    assert [s["干支"] for s in d["大运步"][:4]] == ["丁丑", "戊寅", "己卯", "庚辰"]
    assert d["当前大运"]["干支"] == "己卯"           # 2026 ∈ 2021–2030


def test_liunian_liuyue_2026():
    c = chart(true_solar=False, date="2026-07-01")
    ln = c["流年流月"]
    assert ln["流年"] == "丙午"
    months = [m["干支"] for m in ln["流月"]]
    assert len(months) == 12 and months[0] == "庚寅" and months[-1] == "辛丑"
    assert ln["当前流月"] == "甲午"


def test_wuhu_dun_table():
    assert [m["干支"] for m in liuyue_list("丙")][:2] == ["庚寅", "辛卯"]
    assert liuyue_list("甲")[0]["干支"] == "丙寅"


def test_urumqi_true_solar_flips_day_and_hour():
    urumqi = {"year": 2000, "month": 6, "day": 1, "hour": 0, "minute": 30,
              "lon": 87.62, "lat": 43.83, "tz": "Asia/Shanghai", "gender": "男"}
    on = build_chart({**urumqi, "true_solar": True, "date": "2026-07-01"})
    off = build_chart({**urumqi, "true_solar": False, "date": "2026-07-01"})
    assert on["四柱"]["日柱"]["干支"] != off["四柱"]["日柱"]["干支"]
    assert on["四柱"]["时柱"]["干支"][1] == "亥"     # 真太阳时 22:22 → 亥时
    assert off["四柱"]["时柱"]["干支"][1] == "子"


def test_equation_of_time_reference_points():
    assert -5.0 < equation_of_time_minutes(datetime(2000, 1, 1).date()) < -2.0
    assert 14.0 < equation_of_time_minutes(datetime(2000, 11, 3).date()) < 18.0


def test_true_solar_time_london():
    tst, lon_corr, eot = true_solar_time(datetime(2000, 1, 1, 12, 0), -0.1278, "Europe/London")
    assert tst.hour == 11 and 54 <= tst.minute <= 57
    assert abs(lon_corr - (-0.5)) < 0.2


def test_dst_true_solar_london_july():
    # 夏令时回归锁定：伦敦 7 月 UTC+1 → 时区中央经线 15°E → 经度修正约 -60 分钟
    on = chart(month=7, day=1, true_solar=True, date="2026-07-01")
    off = chart(month=7, day=1, true_solar=False, date="2026-07-01")
    assert on["四柱"]["时柱"]["干支"][1] == "巳"      # 12:00 夏令时钟表时 → 真太阳时 ~10:55
    assert off["四柱"]["时柱"]["干支"][1] == "午"
    assert on["时间处理"]["经度修正分钟"] < -55


def test_unknown_hour_three_pillar_mode():
    c = chart(hour="unknown", true_solar=False, date="2026-07-01")
    assert "时柱" not in c["四柱"]
    assert [c["四柱"][k]["干支"] for k in ("年柱", "月柱", "日柱")] == ["己卯", "丙子", "戊午"]
    assert any("时辰不明" in n for n in c["标注"])


def test_wuxing_counts_abc():
    c = chart(true_solar=False, date="2026-07-01")
    w = c["五行"]["计数"]
    assert sum(w.values()) == 8
    assert w["金"] == 0 and w["土"] == 3 and w["火"] == 3
    assert c["五行"]["月令"] == "子"


def test_json_cli_and_schema(capsys):
    rc = main(["--year", "2000", "--month", "1", "--day", "1", "--hour", "12",
               "--minute", "0", "--lon", "-0.1278", "--lat", "51.5074",
               "--tz", "Europe/London", "--gender", "女",
               "--date", "2026-07-01", "--no-true-solar-time", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert set(data) >= {"输入", "时间处理", "四柱", "五行", "大运", "流年流月", "标注"}


def test_cli_text_output_shows_seed_facts(capsys):
    rc = main(["--year", "2000", "--month", "1", "--day", "1", "--hour", "12",
               "--minute", "0", "--lon", "-0.1278", "--lat", "51.5074",
               "--tz", "Europe/London", "--gender", "女", "--date", "2026-07-01"])
    assert rc == 0
    out = capsys.readouterr().out
    for token in ("己卯", "丙子", "戊午", "真太阳时", "丙午", "己卯"):
        assert token in out


def test_cli_bad_tz_errors(capsys):
    rc = main(["--year", "2000", "--month", "1", "--day", "1", "--hour", "12",
               "--minute", "0", "--lon", "0", "--lat", "0",
               "--tz", "Not/AZone", "--gender", "女"])
    assert rc == 1
    assert "Error" in capsys.readouterr().err
