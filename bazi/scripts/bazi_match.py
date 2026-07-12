"""合八字（八字合盘）脚本 — 干支关系只能由本脚本计算（模型永不推关系）。
双人参数 --a-*/--b-*，无中间文件（真实生辰不落盘）。排盘复用 bazi_chart.build_chart；
关系判定为教科书查表（五合/六合/三合半合/六冲/三刑自刑/六害/相破），表本身即测试对象。
解读方法与伦理见 references/match-method.md（讲动力与功课，不打分、无克夫克妻）。
"""
import argparse
import json
import sys

from bazi_chart import GAN_WUXING, build_chart

GAN = "甲乙丙丁戊己庚辛壬癸"
WUHE = {frozenset("甲己"): "土", frozenset("乙庚"): "金", frozenset("丙辛"): "水",
        frozenset("丁壬"): "木", frozenset("戊癸"): "火"}
LIUHE = {frozenset(p) for p in ("子丑", "寅亥", "卯戌", "辰酉", "巳申", "午未")}
SANHE = {"水": "申子辰", "木": "亥卯未", "火": "寅午戌", "金": "巳酉丑"}
LIUCHONG = {frozenset(p) for p in ("子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥")}
SANXING = ["寅巳申", "丑戌未", "子卯"]
ZIXING = set("辰午酉亥")
LIUHAI = {frozenset(p) for p in ("子未", "丑午", "寅巳", "卯辰", "申亥", "酉戌")}
XIANGPO = {frozenset(p) for p in ("子酉", "午卯", "辰丑", "戌未", "寅亥", "巳申")}
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
SPOUSE = {"女": ("官杀", {"正官", "七杀"}), "男": ("财星", {"正财", "偏财"})}
PILLARS = ["年", "月", "日", "时"]


def gan_relation(ga: str, gb: str) -> str:
    """甲方干 × 乙方干：五合（含化神）/ 同气 / 生克方向（A=甲方，B=乙方）。"""
    if frozenset((ga, gb)) in WUHE:
        return f"五合化{WUHE[frozenset((ga, gb))]}"
    wa, wb = GAN_WUXING[ga], GAN_WUXING[gb]
    if wa == wb:
        return "同气"
    if SHENG[wa] == wb:
        return "A生B"
    if SHENG[wb] == wa:
        return "B生A"
    if KE[wa] == wb:
        return "A克B"
    return "B克A"


def shishen(day_gan: str, other_gan: str) -> str:
    """other_gan 之于 day_gan 的十神。"""
    wd, wo = GAN_WUXING[day_gan], GAN_WUXING[other_gan]
    same = (GAN.index(day_gan) % 2) == (GAN.index(other_gan) % 2)
    if wo == wd:
        return "比肩" if same else "劫财"
    if SHENG[wd] == wo:
        return "食神" if same else "伤官"
    if KE[wd] == wo:
        return "偏财" if same else "正财"
    if KE[wo] == wd:
        return "七杀" if same else "正官"
    return "偏印" if same else "正印"


def zhi_relations(za: str, zb: str) -> list:
    """两支之间全部关系标签（多标签如实全列，如寅亥＝六合＋相破）。"""
    pair = frozenset((za, zb))
    tags = []
    if pair in LIUHE:
        tags.append("六合")
    for wx, trio in SANHE.items():
        if za != zb and za in trio and zb in trio:
            tags.append(f"半合（{trio}{wx}局）")
    if pair in LIUCHONG:
        tags.append("六冲")
    if za == zb and za in ZIXING:
        tags.append("自刑")
    for trio in SANXING:
        if za != zb and za in trio and zb in trio:
            tags.append("相刑")
    if pair in LIUHAI:
        tags.append("相害")
    if pair in XIANGPO:
        tags.append("相破")
    return tags


def _pillars(chart: dict) -> dict:
    """{柱名: 干支} — 三柱盘无时柱。"""
    out = {}
    for name, p in chart["四柱"].items():
        out[name[0]] = p["干支"]           # 年柱→年
    return out


def _overview(chart: dict) -> dict:
    steps = chart["大运"]["大运步"]
    cur = chart["大运"]["当前大运"]
    nxt = None
    for i, s in enumerate(steps):
        if s is cur and i + 1 < len(steps):
            nxt = steps[i + 1]
    def fmt(s):
        return f"{s['干支']}（{s['起止年']}）" if s and "起止年" in s else "未起运"
    return {"四柱": " ".join(p["干支"] for p in chart["四柱"].values()),
            "日主": chart["五行"]["日主"],
            "五行计数": chart["五行"]["计数"],
            "当前大运": fmt(cur), "下一步大运": fmt(nxt)}


def _spouse_raw(chart: dict, gender: str) -> dict:
    label, targets = SPOUSE[gender]
    tou, cang = [], []
    for name, p in chart["四柱"].items():
        pos = name[0]
        if p["天干十神"] in targets:
            tou.append(pos)
        if any(t in targets for t in p["藏干十神"]):
            cang.append(pos)
    kong = chart["五行"]["空亡(日柱旬空)"]
    kong_hit = any(chart["四柱"][f"{pos}柱"]["干支"][1] in kong for pos in cang)
    return {"配偶星": label, "透干位": tou, "藏支位": cang, "坐支逢空": kong_hit}


def build_match(args: dict) -> dict:
    date = args.get("date")
    ts = args.get("true_solar", True)
    ca = build_chart({**args["a"], "date": date, "true_solar": ts})
    cb = build_chart({**args["b"], "date": date, "true_solar": ts})
    pa, pb = _pillars(ca), _pillars(cb)

    gan_hits = []
    for na, gza in pa.items():
        for nb, gzb in pb.items():
            rel = gan_relation(gza[0], gzb[0])
            if rel.startswith("五合"):
                gan_hits.append({"位置": f"甲方{na}干×乙方{nb}干",
                                 "干": f"{gza[0]}×{gzb[0]}", "关系": rel})
    day_rel = gan_relation(pa["日"][0], pb["日"][0])
    gan_hits.append({"位置": "甲方日干×乙方日干",
                     "干": f"{pa['日'][0]}×{pb['日'][0]}", "关系": day_rel})

    zhi_hits = []
    for na, gza in pa.items():
        for nb, gzb in pb.items():
            tags = zhi_relations(gza[1], gzb[1])
            if tags or (na == "日" and nb == "日") or (na == "年" and nb == "年"):
                zhi_hits.append({"位置": f"甲方{na}支×乙方{nb}支",
                                 "支": f"{gza[1]}×{gzb[1]}", "关系": tags})

    dz = zhi_relations(pa["日"][1], pb["日"][1])
    gtag = ("天干五合" if day_rel.startswith("五合") else
            "天干同气" if day_rel == "同气" else
            "天干相生" if "生" in day_rel else "天干相克")
    if not dz:
        ztag = "地支无明显关系"
    elif "六合" in dz or any(t.startswith("半合") for t in dz):
        ztag = "地支相合"
    elif "六冲" in dz:
        ztag = "地支相冲"
    elif "相害" in dz:
        ztag = "地支相害"
    elif "自刑" in dz or "相刑" in dz:
        ztag = "地支相刑"
    else:
        ztag = "地支相破"
    verdict = {"判定": f"{gtag}、{ztag}", "日干关系": day_rel,
               "互为十神": {"乙方日干之于甲方": shishen(pa["日"][0], pb["日"][0]),
                            "甲方日干之于乙方": shishen(pb["日"][0], pa["日"][0])}}

    ova, ovb = _overview(ca), _overview(cb)
    sync = {"甲方": {"当前": ova["当前大运"], "下一步": ova["下一步大运"]},
            "乙方": {"当前": ovb["当前大运"], "下一步": ovb["下一步大运"]},
            "当前同干支": ova["当前大运"][:2] == ovb["当前大运"][:2]}

    notices = ["关系判定为教科书查表（多标签如实全列）；解读口径见 references/match-method.md——"
               "讲动力与功课，不打分、不判吉凶。"]
    for side, c in (("甲方", ca), ("乙方", cb)):
        for n in c["标注"]:
            if "时辰不明" in n:
                notices.append(f"{side}{n}")

    return {"甲方": ova, "乙方": ovb, "天干互动": gan_hits, "地支互动": zhi_hits,
            "日柱判定": verdict,
            "夫妻星": {"甲方": _spouse_raw(ca, args["a"]["gender"]),
                       "乙方": _spouse_raw(cb, args["b"]["gender"])},
            "大运同频": sync, "参考日期": date or "", "标注": notices}


def _print_text(m: dict, la: str, lb: str) -> None:
    for key, label in (("甲方", la), ("乙方", lb)):
        o = m[key]
        print(f"# {label}：{o['四柱']}｜日主 {o['日主']}｜当前大运 {o['当前大运']}"
              f"（下一步 {o['下一步大运']}）")
    d = m["日柱判定"]
    hu = d["互为十神"]
    print(f"\n## 日柱判定：{d['判定']}（{d['日干关系']}；"
          f"{lb}日干是{la}的{hu['乙方日干之于甲方']}、{la}日干是{lb}的{hu['甲方日干之于乙方']}）")
    print("\n## 天干互动")
    for e in m["天干互动"]:
        print(f"- {e['位置']} {e['干']}：{e['关系']}")
    print("\n## 地支互动")
    for e in m["地支互动"]:
        rel = "、".join(e["关系"]) if e["关系"] else "无明显关系"
        print(f"- {e['位置']} {e['支']}：{rel}")
    print("\n## 夫妻星原料")
    for key, label in (("甲方", la), ("乙方", lb)):
        s = m["夫妻星"][key]
        print(f"- {label}（{s['配偶星']}）：透干位 {s['透干位'] or '无'}｜"
              f"藏支位 {s['藏支位'] or '无'}｜坐支逢空 {'是' if s['坐支逢空'] else '否'}")
    sy = m["大运同频"]
    print(f"\n## 大运同频：{la} {sy['甲方']['当前']}→{sy['甲方']['下一步']}；"
          f"{lb} {sy['乙方']['当前']}→{sy['乙方']['下一步']}"
          f"｜当前同干支：{'是' if sy['当前同干支'] else '否'}")
    print("\n## 标注")
    for n in m["标注"]:
        print(f"- {n}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="合八字（八字合盘）：双人干支互动计算。方法见 references/match-method.md。")
    for side in ("a", "b"):
        ap.add_argument(f"--{side}-year", type=int, required=True)
        ap.add_argument(f"--{side}-month", type=int, required=True)
        ap.add_argument(f"--{side}-day", type=int, required=True)
        ap.add_argument(f"--{side}-hour", required=True)
        ap.add_argument(f"--{side}-minute", default="0")
        ap.add_argument(f"--{side}-lon", type=float, required=True)
        ap.add_argument(f"--{side}-lat", type=float, default=None)
        ap.add_argument(f"--{side}-tz", required=True)
        ap.add_argument(f"--{side}-gender", required=True, choices=["男", "女"])
    ap.add_argument("--a-label", default="甲方")
    ap.add_argument("--b-label", default="乙方")
    ap.add_argument("--date", default=None)
    ap.add_argument("--no-true-solar-time", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        v = vars(args)
        def person(side):
            return {k: v[f"{side}_{k}"] for k in
                    ("year", "month", "day", "hour", "minute", "lon", "lat", "tz", "gender")}
        m = build_match({"a": person("a"), "b": person("b"), "date": args.date,
                         "true_solar": not args.no_true_solar_time})
    except Exception as e:  # noqa: BLE001 — clean message, no traceback
        print(f"Error: {e}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(m, ensure_ascii=False, indent=1))
    else:
        _print_text(m, args.a_label, args.b_label)
    return 0


if __name__ == "__main__":
    sys.exit(main())
