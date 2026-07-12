#!/usr/bin/env python3
"""宿曜占星排宿脚本——本命宿 / 三九相性 / 日运（二十七宿，无牛宿）。

出生只需日期，不需时辰。真实生辰仅经 CLI 参数进内存，不落盘。

单人:  python xiuyao_chart.py --year 2000 --month 1 --day 1 [--date 2026-07-01] [--json]
双人:  加 --b-year 1995 --b-month 6 --b-day 15 [--label 甲方] [--b-label 乙方]
"""
import argparse
import json
import sys
from datetime import date as _date

from lunar_python import Solar

CYCLE = ["昴", "毕", "觜", "参", "井", "鬼", "柳", "星", "张", "翼", "轸", "角", "亢",
         "氐", "房", "心", "尾", "箕", "斗", "女", "虚", "危", "室", "壁", "奎", "娄", "胃"]
ANCHOR = {1: "室", 2: "奎", 3: "胃", 4: "毕", 5: "参", 6: "鬼",
          7: "张", 8: "角", 9: "氐", 10: "心", 11: "斗", 12: "虚"}
REL_SEQ = {1: "荣", 2: "衰", 3: "安", 4: "危", 5: "成", 6: "坏", 7: "友", 8: "亲"}
PAIR_NAME = {"荣": "荣亲", "亲": "荣亲", "友": "友衰", "衰": "友衰",
             "安": "安坏", "坏": "安坏", "危": "危成", "成": "危成",
             "业": "业胎", "胎": "业胎", "命": "命"}
GROUPS = {"东方青龙": ["角", "亢", "氐", "房", "心", "尾", "箕"],
          "北方玄武": ["斗", "女", "虚", "危", "室", "壁"],
          "西方白虎": ["奎", "娄", "胃", "昴", "毕", "觜", "参"],
          "南方朱雀": ["井", "鬼", "柳", "星", "张", "翼", "轸"]}
LIUHAI_OFFSETS = {0: "命", 3: "意", 9: "事", 12: "克", 15: "聚", 19: "同"}

NOTES = [
    "相性与日运为宿曜传统结构描述，讲关系动力与功课，不判吉凶定数、不打分。",
    "六害位之凶传统上重在凌犯期间；本脚本不推凌犯（需行星数据），六害仅作结构提示/谨慎日参考。",
    "农历换算按中国农历（lunar-python）；历法边界（朔时刻、日中旧历差异）可能使边界日期差一宿。",
]


def benming_xiu(year, month, day):
    """公历日期 → 本命宿（也用于任意日期的值日宿）。"""
    _date(year, month, day)  # 先校验真实日期——lunar-python 对 2/31 之类会静默滚动
    lunar = Solar.fromYmd(year, month, day).getLunar()
    lm, ld = lunar.getMonth(), lunar.getDay()
    leap = lm < 0
    lm = abs(lm)  # 闰月取本月锚
    xiu = CYCLE[(CYCLE.index(ANCHOR[lm]) + ld - 1) % 27]
    group = next(g for g, xs in GROUPS.items() if xiu in xs)
    lunar_str = (f"农历{lunar.getYearInChinese()}年"
                 f"{'闰' if leap else ''}{lunar.getMonthInChinese()}月{lunar.getDayInChinese()}")
    return {"宿": xiu, "农历": lunar_str, "四象组": group, "闰月": leap}


def relation(a, b):
    """从 a 的本命宿看 b：三九关系 + 近/中/远距离。"""
    d = (CYCLE.index(b) - CYCLE.index(a)) % 27
    if d == 0:
        return {"关系": "命", "距离": None}
    if d == 9:
        return {"关系": "业", "距离": None}
    if d == 18:
        return {"关系": "胎", "距离": None}
    s = min(d, 27 - d)
    dist = "近" if s <= 4 else ("中" if s <= 8 else "远")
    return {"关系": REL_SEQ[d % 9], "距离": dist}


def liuhai_name(benming, other):
    """other 是否处于 benming 的六害位；是则返回名称（命/意/事/克/聚/同），否则 None。"""
    d = (CYCLE.index(other) - CYCLE.index(benming)) % 27
    return LIUHAI_OFFSETS.get(d)


def _fmt_rel(rel):
    if rel["距离"] is None:
        return f"{rel['关系']}（{PAIR_NAME[rel['关系']]}）"
    return f"{rel['关系']}（{rel['距离']}距离·{PAIR_NAME[rel['关系']]}组）"


def build(args):
    a = benming_xiu(args.year, args.month, args.day)
    out = {"甲方": a, "标注": NOTES, "参考日期": args.date}
    if args.b_year is not None:
        b = benming_xiu(args.b_year, args.b_month, args.b_day)
        out["乙方"] = b
        out["相性"] = {"甲方看乙方": relation(a["宿"], b["宿"]),
                       "乙方看甲方": relation(b["宿"], a["宿"])}
    y, m, d = (int(x) for x in args.date.split("-"))
    day_xiu = benming_xiu(y, m, d)
    daily = {"值日宿": day_xiu["宿"], "农历": day_xiu["农历"],
             "甲方": {"关系": relation(a["宿"], day_xiu["宿"]),
                      "六害位": liuhai_name(a["宿"], day_xiu["宿"])}}
    if "乙方" in out:
        daily["乙方"] = {"关系": relation(out["乙方"]["宿"], day_xiu["宿"]),
                         "六害位": liuhai_name(out["乙方"]["宿"], day_xiu["宿"])}
    out["日运"] = daily
    return out


def render(out, label_a, label_b):
    lines = []
    a = out["甲方"]
    lines.append(f"【{label_a}】{a['农历']}　本命宿：{a['宿']}宿（{a['四象组']}）")
    if "乙方" in out:
        b = out["乙方"]
        lines.append(f"【{label_b}】{b['农历']}　本命宿：{b['宿']}宿（{b['四象组']}）")
        rel = out["相性"]
        lines.append(f"【三九相性】{label_a}看{label_b}：{_fmt_rel(rel['甲方看乙方'])}"
                     f"　/　{label_b}看{label_a}：{_fmt_rel(rel['乙方看甲方'])}")
    d = out["日运"]
    seg = [f"值日宿：{d['值日宿']}宿（{d['农历']}）"]
    for key, label in (("甲方", label_a), ("乙方", label_b)):
        if key in d:
            r = _fmt_rel(d[key]["关系"])
            lh = d[key]["六害位"]
            seg.append(f"{label}：{r}" + (f"·六害位「{lh}」" if lh else ""))
    lines.append(f"【日运 {out['参考日期']}】" + "；".join(seg))
    lines.append("【标注】" + " ".join(f"{i}) {n}" for i, n in enumerate(NOTES, 1)))
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description="宿曜占星排宿（27 宿）")
    p.add_argument("--year", type=int, required=True)
    p.add_argument("--month", type=int, required=True)
    p.add_argument("--day", type=int, required=True)
    p.add_argument("--b-year", type=int, dest="b_year")
    p.add_argument("--b-month", type=int, dest="b_month")
    p.add_argument("--b-day", type=int, dest="b_day")
    p.add_argument("--label", default="甲方")
    p.add_argument("--b-label", dest="b_label", default="乙方")
    p.add_argument("--date", default=_date.today().isoformat())
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    b_fields = [args.b_year, args.b_month, args.b_day]
    if any(x is not None for x in b_fields) and any(x is None for x in b_fields):
        print("错误：--b-year/--b-month/--b-day 必须同时提供", file=sys.stderr)
        return 1
    try:
        out = build(args)
    except Exception as e:  # 非法日期等
        print(f"错误：{e}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(render(out, args.label, args.b_label))
    return 0


if __name__ == "__main__":
    sys.exit(main())
