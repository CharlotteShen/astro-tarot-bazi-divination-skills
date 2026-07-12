"""八字排盘脚本 — 干支只能由本脚本计算（模型永不排盘）。
lunar-python 负责四柱/藏干/十神/空亡/大运；真太阳时（经度修正+Spencer 均时差）与流月
（五虎遁）在本脚本内实现。流派约定见 references/conventions.md：
--sect mainstream（默认：晚子时不换日柱）| traditional（子时整体归次日）。
输出中文为主；--json 输出结构化数据；时辰不明用 --hour unknown（三柱盘+可靠性标注）。
"""
import argparse
import json
import math
import sys
from datetime import date as _date
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from lunar_python import Solar

GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
GAN_WUXING = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
              "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
ZHI_WUXING = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
              "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}
# 五虎遁：年干 → 正月（寅月）月干
WUHU_DUN = {"甲": "丙", "己": "丙", "乙": "戊", "庚": "戊", "丙": "庚",
            "辛": "庚", "丁": "壬", "壬": "壬", "戊": "甲", "癸": "甲"}
YUE_ZHI = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]
JIEQI = ["立春", "惊蛰", "清明", "立夏", "芒种", "小暑",
         "立秋", "白露", "寒露", "立冬", "大雪", "小寒"]
SECT = {"mainstream": 2, "traditional": 1}   # lunar-python setSect 映射（原型实测）


def equation_of_time_minutes(d) -> float:
    """Spencer 近似均时差（分钟）。误差远小于一个时辰（2 小时），见 conventions.md。"""
    b = 2 * math.pi * (d.timetuple().tm_yday - 81) / 364
    return 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)


def true_solar_time(local_dt: datetime, lon: float, tz: str):
    """钟表时 → 真太阳时。返回 (真太阳时, 经度修正分钟, 均时差分钟)。"""
    aware = local_dt.replace(tzinfo=ZoneInfo(tz))
    meridian = 15 * aware.utcoffset().total_seconds() / 3600   # 时区中央经线（含夏令时）
    lon_corr = 4 * (lon - meridian)
    eot = equation_of_time_minutes(local_dt.date())
    return local_dt + timedelta(minutes=lon_corr + eot), lon_corr, eot


def liuyue_list(liunian_gan: str) -> list:
    """五虎遁：流年干 → 12 个流月干支（寅月起，节气分月）。"""
    start = GAN.index(WUHU_DUN[liunian_gan])
    return [{"节": JIEQI[i], "干支": GAN[(start + i) % 10] + YUE_ZHI[i]}
            for i in range(12)]


def _pillar(gz: str, hide: list, shishen_gan: str, shishen_zhi: list, nayin: str) -> dict:
    return {"干支": gz, "藏干": list(hide), "天干十神": shishen_gan,
            "藏干十神": list(shishen_zhi), "纳音": nayin}


def build_chart(a: dict) -> dict:
    notices = []
    unknown_hour = str(a["hour"]) == "unknown"
    hour = 12 if unknown_hour else int(a["hour"])
    minute = 0 if unknown_hour else int(a["minute"])
    birth = datetime(int(a["year"]), int(a["month"]), int(a["day"]), hour, minute)

    time_block = {"输入时间": birth.strftime("%Y-%m-%d %H:%M"), "时区": a["tz"]}
    if unknown_hour:
        notices.append("时辰不明：仅排三柱（年/月/日），时柱与真太阳时不适用；"
                       "身强弱与大运起运按正午近似（误差见 conventions.md）。")
        used = birth
        time_block["真太阳时"] = "不适用（时辰不明）"
    elif a.get("true_solar", True):
        used, lon_corr, eot = true_solar_time(birth, float(a["lon"]), a["tz"])
        time_block.update({"真太阳时": used.strftime("%Y-%m-%d %H:%M"),
                           "经度修正分钟": round(lon_corr, 1),
                           "均时差分钟": round(eot, 1)})
        notices.append("时柱按真太阳时排定（经度修正+均时差）；--no-true-solar-time 可关闭。")
    else:
        used = birth
        time_block["真太阳时"] = "未启用（--no-true-solar-time）"

    solar = Solar.fromYmdHms(used.year, used.month, used.day, used.hour, used.minute, 0)
    lunar = solar.getLunar()
    ec = lunar.getEightChar()
    sect_key = a.get("sect", "mainstream")
    ec.setSect(SECT[sect_key])
    notices.append(f"子时流派：{sect_key}"
                   f"（{'晚子时不换日柱' if sect_key == 'mainstream' else '子时整体归次日'}）。")

    pillars = {
        "年柱": _pillar(ec.getYear(), ec.getYearHideGan(), ec.getYearShiShenGan(),
                        ec.getYearShiShenZhi(), ec.getYearNaYin()),
        "月柱": _pillar(ec.getMonth(), ec.getMonthHideGan(), ec.getMonthShiShenGan(),
                        ec.getMonthShiShenZhi(), ec.getMonthNaYin()),
        "日柱": _pillar(ec.getDay(), ec.getDayHideGan(), "日主",
                        ec.getDayShiShenZhi(), ec.getDayNaYin()),
    }
    if not unknown_hour:
        pillars["时柱"] = _pillar(ec.getTime(), ec.getTimeHideGan(), ec.getTimeShiShenGan(),
                                  ec.getTimeShiShenZhi(), ec.getTimeNaYin())

    chars = "".join(p["干支"] for p in pillars.values())
    counts = {w: 0 for w in ("木", "火", "土", "金", "水")}
    for ch in chars:
        counts[GAN_WUXING.get(ch) or ZHI_WUXING[ch]] += 1
    wuxing = {"计数": counts, "月令": pillars["月柱"]["干支"][1],
              "日主": pillars["日柱"]["干支"][0],
              "空亡(日柱旬空)": ec.getDayXunKong()}

    gender = a["gender"]
    yun = ec.getYun(1 if gender == "男" else 0)
    forward = yun.isForward() if hasattr(yun, "isForward") else True
    steps = []
    for dy in yun.getDaYun()[1:11]:
        steps.append({"起始虚岁": dy.getStartAge(), "干支": dy.getGanZhi(),
                      "起止年": f"{dy.getStartYear()}–{dy.getEndYear()}"})
    ref_date = datetime.strptime(a.get("date") or _date.today().isoformat(), "%Y-%m-%d")
    current = next((s for s in steps
                    if int(s["起止年"].split("–")[0]) <= ref_date.year
                    <= int(s["起止年"].split("–")[1])), None)
    dayun = {"方向": "顺排" if forward else "逆排",
             "起运": f"{yun.getStartYear()}年{yun.getStartMonth()}个月{yun.getStartDay()}天"
                     f"（约 {yun.getStartSolar().toYmd()}）",
             "大运步": steps,
             "当前大运": current or {"干支": "未起运"}}
    notices.append("起运按 3 天折 1 年标准算法（lunar-python）。")
    if unknown_hour:
        notices.append("时辰不明时起运岁数按正午近似；每偏 1 时辰约 ±10 天，最坏约 ±2 个月。")

    # --date 是整日日期，取正午消歧：恰逢立春日且立春时刻在午后时，全日按立春前流年计
    ref_lunar = Solar.fromYmdHms(ref_date.year, ref_date.month, ref_date.day, 12, 0, 0).getLunar()
    liunian = ref_lunar.getYearInGanZhiExact()
    months = liuyue_list(liunian[0])
    liuyue_now = ref_lunar.getMonthInGanZhiExact()
    liu = {"参考日期": ref_date.strftime("%Y-%m-%d"), "流年": liunian,
           "流月": months, "当前流月": liuyue_now}

    return {"输入": {"公历": birth.strftime("%Y-%m-%d") +
                     ("（时辰不明）" if unknown_hour else birth.strftime(" %H:%M")),
                     "性别": gender, "经度": a["lon"], "纬度": a.get("lat"),
                     "时区": a["tz"], "子时流派": sect_key},
            "时间处理": time_block, "四柱": pillars, "五行": wuxing,
            "大运": dayun, "流年流月": liu, "标注": notices}


def _print_text(c: dict) -> None:
    print(f"# 八字排盘 — {c['输入']['公历']}（{c['输入']['性别']}命）")
    for k, v in c["时间处理"].items():
        print(f"- {k}: {v}")
    print("\n## 四柱")
    for name, p in c["四柱"].items():
        print(f"- {name} {p['干支']}｜藏干 {'、'.join(p['藏干'])}"
              f"｜十神 {p['天干十神']}（藏干：{'、'.join(p['藏干十神'])}）｜纳音 {p['纳音']}")
    w = c["五行"]
    print(f"\n## 五行  日主 {w['日主']}｜月令 {w['月令']}｜空亡 {w['空亡(日柱旬空)']}")
    print("- 计数: " + "  ".join(f"{k}{v}" for k, v in w["计数"].items()))
    d = c["大运"]
    print(f"\n## 大运（{d['方向']}，起运 {d['起运']}）")
    for s in d["大运步"]:
        cur = " ←当前" if s == d["当前大运"] else ""
        print(f"- {s['起始虚岁']}岁 {s['干支']} {s['起止年']}{cur}")
    ln = c["流年流月"]
    print(f"\n## 流年流月（参考日期 {ln['参考日期']}）")
    print(f"- 流年 {ln['流年']}｜当前流月 {ln['当前流月']}")
    print("- 流月: " + "  ".join(f"{m['节']}{m['干支']}" for m in ln["流月"]))
    print("\n## 标注")
    for n in c["标注"]:
        print(f"- {n}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="八字排盘（lunar-python；真太阳时与流派约定见 references/conventions.md）")
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--month", type=int, required=True)
    ap.add_argument("--day", type=int, required=True)
    ap.add_argument("--hour", required=True, help="0-23，或 unknown（时辰不明→三柱盘）")
    ap.add_argument("--minute", default="0")
    ap.add_argument("--lon", type=float, required=True, help="出生地经度，东正西负")
    ap.add_argument("--lat", type=float, default=None, help="纬度（仅记录，不参与计算）")
    ap.add_argument("--tz", required=True, help="IANA 时区，如 Asia/Shanghai")
    ap.add_argument("--gender", required=True, choices=["男", "女"], help="用于大运顺逆")
    ap.add_argument("--date", default=None, help="分析参考日期 YYYY-MM-DD（默认今天）；锁定后输出完全确定")
    ap.add_argument("--no-true-solar-time", action="store_true")
    ap.add_argument("--sect", default="mainstream", choices=list(SECT))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        chart = build_chart({"year": args.year, "month": args.month, "day": args.day,
                             "hour": args.hour, "minute": args.minute,
                             "lon": args.lon, "lat": args.lat, "tz": args.tz,
                             "gender": args.gender, "date": args.date,
                             "true_solar": not args.no_true_solar_time,
                             "sect": args.sect})
    except Exception as e:  # noqa: BLE001 — clean message, no traceback
        print(f"Error: {e}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(chart, ensure_ascii=False, indent=1))
    else:
        _print_text(chart)
    return 0


if __name__ == "__main__":
    sys.exit(main())
