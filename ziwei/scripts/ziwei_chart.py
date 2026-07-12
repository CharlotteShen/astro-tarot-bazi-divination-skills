"""紫微斗数排盘脚本 — 安星只能由本脚本计算（模型永不安星）。
引擎 iztro-py（纯 Python，MIT）；安星诀手工推演验证吻合（见 v3.1.0 spec §8）。
0.3.5 的 i18n 管线损坏但 zh_CN 翻译表随包存在，本脚本自带查表 shim（测试钉死输出无未翻译 key）。
真太阳时复用 bazi_chart 的同一已验证实现。流派约定见 references/conventions.md
（三合派为主+四化层、闰月 fix_leap 对半拆式、出生地当地真太阳时定时辰）。
"""
import argparse
import json
import os
import sys
from datetime import date as _date
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "bazi", "scripts"))
from bazi_chart import true_solar_time  # noqa: E402 — 单一已验证实现（跨技能导入，用户核准）

from iztro_py.astro import by_solar_hour  # noqa: E402
from iztro_py.i18n.locales.zh_CN import translations  # noqa: E402

ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


def _flatten(d: dict, out: dict = None) -> dict:
    """i18n shim：把嵌套翻译表按叶 key 扁平化（153 条、无叶键冲突——原型实测）。"""
    if out is None:
        out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            _flatten(v, out)
        else:
            out[k] = v
    return out


ZH = _flatten(translations)


def zh(key: str) -> str:
    """内部 key → 中文；已是中文或未收录者原样返回。"""
    return ZH.get(key, key)


def _hour_branch(hour: int) -> str:
    return ZHI[((hour + 1) // 2) % 12]


def _stars(star_list) -> list:
    return [{"名": zh(s.name), "亮度": s.brightness or "",
             "生年四化": s.mutagen or ""} for s in star_list]


def build_chart(a: dict) -> dict:
    if str(a["hour"]) == "unknown":
        raise ValueError("紫微斗数必须有出生时辰才能安命宫；时辰不明请补时辰，或改用八字三柱盘。")
    birth = datetime(int(a["year"]), int(a["month"]), int(a["day"]),
                     int(a["hour"]), int(a.get("minute") or 0))
    notices = []
    time_block = {"输入时间": birth.strftime("%Y-%m-%d %H:%M"), "时区": a["tz"]}
    if a.get("true_solar", True):
        used, lon_corr, eot = true_solar_time(birth, float(a["lon"]), a["tz"])
        time_block.update({"真太阳时": used.strftime("%Y-%m-%d %H:%M"),
                           "经度修正分钟": round(lon_corr, 1),
                           "均时差分钟": round(eot, 1)})
        notices.append("时辰按出生地真太阳时排定（海外出生不换算北京时间）；"
                       "--no-true-solar-time 可关闭。")
        if _hour_branch(used.hour) != _hour_branch(birth.hour):
            notices.append(f"注意：真太阳时修正改变了时辰（{_hour_branch(birth.hour)}时→"
                           f"{_hour_branch(used.hour)}时），属边界出生，建议两种模式各排一次对比。")
    else:
        used = birth
        time_block["真太阳时"] = "未启用（--no-true-solar-time）"
    astrolabe = by_solar_hour(f"{used.year}-{used.month}-{used.day}", used.hour, a["gender"])
    notices.append("闰月按引擎 fix_leap=True（对半拆式归属）；流派：三合派为主+四化层。")

    palaces = []
    for p in astrolabe.palaces:
        palaces.append({"宫名": zh(p.name),
                        "干支": zh(p.heavenly_stem) + zh(p.earthly_branch),
                        "主星": _stars(p.major_stars),
                        "辅星": _stars(p.minor_stars),
                        "杂曜": [zh(s.name) for s in p.adjective_stars],
                        "大限": f"{p.decadal.range[0]}–{p.decadal.range[1]}",
                        "身宫": bool(p.is_body_palace)})

    ref = a.get("date") or _date.today().isoformat()
    h = astrolabe.horoscope(ref)

    def _scope(s) -> dict:
        pal = astrolabe.palaces[s.index]
        return {"宫位": zh(pal.name),
                "干支": zh(s.heavenly_stem) + zh(s.earthly_branch),
                "四化(禄权科忌)": [zh(m) for m in s.mutagen]}

    da = _scope(h.decadal)
    r = astrolabe.palaces[h.decadal.index].decadal.range
    da["起讫岁"] = f"{r[0]}–{r[1]}"

    return {"基本": {"阳历": astrolabe.solar_date, "农历": astrolabe.lunar_date,
                     "时辰": f"{astrolabe.time} {astrolabe.time_range}",
                     "性别": a["gender"], "命主": zh(astrolabe.soul),
                     "身主": zh(astrolabe.body),
                     "五行局": astrolabe.five_elements_class},
            "时间处理": time_block, "十二宫": palaces,
            "大限": da, "流年": _scope(h.yearly), "流月": _scope(h.monthly),
            "参考日期": ref, "标注": notices}


def _star_str(s: dict) -> str:
    mark = f"[{s['生年四化']}]" if s["生年四化"] else ""
    bright = f"({s['亮度']})" if s["亮度"] else ""
    return f"{s['名']}{bright}{mark}"


def _print_text(c: dict) -> None:
    b = c["基本"]
    print(f"# 紫微斗数排盘 — {b['阳历']}（{b['性别']}命）")
    print(f"- 农历 {b['农历']}｜{b['时辰']}｜五行局 {b['五行局']}"
          f"｜命主 {b['命主']}｜身主 {b['身主']}")
    for k, v in c["时间处理"].items():
        print(f"- {k}: {v}")
    print("\n## 十二宫")
    for p in c["十二宫"]:
        majors = "、".join(_star_str(s) for s in p["主星"]) or "（空宫）"
        line = (f"- {p['宫名']}{'〔身宫〕' if p['身宫'] else ''} {p['干支']}"
                f"｜大限 {p['大限']}｜主星 {majors}")
        minors = "、".join(_star_str(s) for s in p["辅星"])
        if minors:
            line += f"｜辅星 {minors}"
        if p["杂曜"]:
            line += f"｜杂曜 {'、'.join(p['杂曜'])}"
        print(line)
    print(f"\n## 三层运限（参考日期 {c['参考日期']}，四化序＝禄权科忌）")
    da = c["大限"]
    print(f"- 大限：{da['宫位']} {da['干支']}（{da['起讫岁']}岁）｜四化 "
          + "、".join(da["四化(禄权科忌)"]))
    for label in ("流年", "流月"):
        s = c[label]
        print(f"- {label}：{s['宫位']} {s['干支']}｜四化 " + "、".join(s["四化(禄权科忌)"]))
    print("\n## 标注")
    for n in c["标注"]:
        print(f"- {n}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="紫微斗数排盘（iztro-py；约定见 references/conventions.md）")
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--month", type=int, required=True)
    ap.add_argument("--day", type=int, required=True)
    ap.add_argument("--hour", required=True, help="0-23；紫微必须有时辰（unknown 会报错）")
    ap.add_argument("--minute", default="0")
    ap.add_argument("--lon", type=float, required=True, help="出生地经度，东正西负")
    ap.add_argument("--lat", type=float, default=None, help="纬度（仅记录，不参与计算）")
    ap.add_argument("--tz", required=True, help="IANA 时区，如 Asia/Shanghai")
    ap.add_argument("--gender", required=True, choices=["男", "女"], help="用于大限顺逆")
    ap.add_argument("--date", default=None,
                    help="分析参考日期 YYYY-MM-DD（默认今天）；锁定后输出完全确定")
    ap.add_argument("--no-true-solar-time", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        chart = build_chart({"year": args.year, "month": args.month, "day": args.day,
                             "hour": args.hour, "minute": args.minute,
                             "lon": args.lon, "lat": args.lat, "tz": args.tz,
                             "gender": args.gender, "date": args.date,
                             "true_solar": not args.no_true_solar_time})
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
