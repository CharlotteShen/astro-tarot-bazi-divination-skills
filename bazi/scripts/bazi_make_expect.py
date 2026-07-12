"""八字评测期望骨架生成器 — 从 fixture 的钉死生辰+参考日期重算盘面（--date 钉死 → ground truth
永久确定），输出 must_mention/forbidden 骨架到 stdout；作者手调后提交（tarot make_expect 同一
模式）。像 bazi_chart.py 一样从不写文件。
"""
import argparse
import json
import sys

from bazi_chart import build_chart

# 捉造诱饵候选：任何出现在 四柱∪大运十步∪流年∪12流月 的候选都会被筛除，取剩余前 3 个。
# 大运步与流月是解读可以合法引用的干支，绝不能当诱饵。
DECOY_CANDIDATES = ["甲子", "乙丑", "丁亥", "壬申", "癸酉", "辛未"]

# voice-and-ethics.md 红线的可正则化词表：刻意只选"否定式罕见"的具体灾祸词——
# 命中注定 之类会出现在免责句（"并非命中注定"）里，留给人工 rubric。
# 每个词都用环视 (?<![/、])X(?![/、]) 排除紧邻 / 或 、 的出现：免责句枚举（"医疗/法律/财务/寿夭"）
# 不再误报；代价是 "血光/破财" 这类连用断言同样放行，连同引号引用、"与"连接等残余，交给人工 rubric。
REDLINES = [
    {"desc": "红线: 血光", "patterns": [r"(?<![/、])血光(?![/、])"]},
    {"desc": "红线: 破财", "patterns": [r"(?<![/、])破财(?![/、])"]},
    {"desc": "红线: 病灾", "patterns": [r"(?<![/、])病灾(?![/、])"]},
    {"desc": "红线: 克夫/克妻", "patterns": [r"(?<![/、])克夫(?![/、])", r"(?<![/、])克妻(?![/、])"]},
    {"desc": "红线: 寿夭/短命", "patterns": [r"(?<![/、])寿夭(?![/、])", r"(?<![/、])短命(?![/、])"]},
]


def chart_tokens(chart: dict) -> set:
    """盘面所有可合法引用的干支：四柱 ∪ 大运十步 ∪ 流年 ∪ 12 流月。"""
    tokens = {p["干支"] for p in chart["四柱"].values()}
    tokens |= {s["干支"] for s in chart["大运"]["大运步"]}
    tokens.add(chart["流年流月"]["流年"])
    tokens |= {m["干支"] for m in chart["流年流月"]["流月"]}
    return tokens


def build_expect(fx: dict) -> dict:
    chart = build_chart({**fx["birth"], "date": fx["date"], "true_solar": True})
    rizhu = chart["五行"]["日主"]
    must = []
    seen = set()
    for p in chart["四柱"].values():
        if p["干支"] not in seen:       # 日/时柱同字（如戊午×2）只出一个 item
            seen.add(p["干支"])
            must.append({"desc": f"四柱: {p['干支']}", "patterns": [p["干支"]]})
    must.append({"desc": f"日主{rizhu}",
                 "patterns": [rf"日主[^。]{{0,10}}{rizhu}", rf"日元[^。]{{0,10}}{rizhu}",
                              rf"{rizhu}(土|木|火|金|水)日主"]})
    must.append({"desc": "身强弱结论（骨架按身强出样——写死前按三得法/打分法核对方向）",
                 "patterns": [rf"(身|日主|{rizhu})[^。]{{0,30}}(偏强|身强|较强)"]})
    must.append({"desc": "身强弱依据关键词",
                 "patterns": ["月令", "得令", "得地", "通根", "得势"]})
    must.append({"desc": "喜用神表述", "patterns": ["喜用神", "用神", "喜神"]})
    cur = chart["大运"]["当前大运"].get("干支", "")
    must.append({"desc": f"当前大运{cur}",
                 "patterns": [rf"大运[^。]{{0,20}}{cur}", rf"{cur}[^。]{{0,10}}大运",
                              rf"{cur}[^。]{{0,15}}20\d\d"]})
    ln = chart["流年流月"]["流年"]
    must.append({"desc": f"流年{ln}",
                 "patterns": [rf"流年[^。]{{0,15}}{ln}", rf"{ln}[^。]{{0,10}}流年",
                              rf"20\d\d[^。]{{0,15}}{ln}"]})
    tokens = chart_tokens(chart)
    decoys = [d for d in DECOY_CANDIDATES if d not in tokens][:3]
    forbidden = [{"desc": f"捉造: {d}", "patterns": [d]} for d in decoys] + REDLINES
    return {"reading_type": "bazi", "must_mention": must,
            "forbidden": forbidden, "must_flag": []}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="八字评测期望骨架生成器（stdout 输出；手调后提交）。")
    ap.add_argument("--fixture", required=True,
                    help="fixture 输入 JSON（birth/date/question/language）")
    args = ap.parse_args(argv)
    try:
        with open(args.fixture, encoding="utf-8") as f:
            fx = json.load(f)
        expect = build_expect(fx)
    except Exception as e:  # noqa: BLE001 — clean message, no traceback
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print(json.dumps(expect, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
