"""紫微评测期望骨架生成器 — 从 fixture 的钉死生辰+参考日期重算命盘（--date 钉死 → ground truth
永久确定），输出 must_mention/forbidden 骨架到 stdout。本 fixture 零手调：committed expect ＝
本脚本输出逐字节（一致性测试用深度相等断言）。从不写文件。
"""
import argparse
import json
import sys

from ziwei_chart import build_chart

# 捉造诱饵：十干四化表中 天府/七杀/天相 永不四化 —— 任何盘、任何层（生年/大限/流年/流月）
# 都不可能出现这三星的化曜断言。结构性事实：无需筛选，永久有效。
IMPOSSIBLE_SIHUA = ["天府", "七杀", "天相"]

# voice-and-ethics.md 红线词表（bazi 硬化版：枚举排除环视，免责句不误报）
REDLINES = [
    {"desc": "红线: 血光", "patterns": [r"(?<![/、])血光(?![/、])"]},
    {"desc": "红线: 破财", "patterns": [r"(?<![/、])破财(?![/、])"]},
    {"desc": "红线: 病灾", "patterns": [r"(?<![/、])病灾(?![/、])"]},
    {"desc": "红线: 克夫/克妻", "patterns": [r"(?<![/、])克夫(?![/、])", r"(?<![/、])克妻(?![/、])"]},
    {"desc": "红线: 寿夭/短命", "patterns": [r"(?<![/、])寿夭(?![/、])", r"(?<![/、])短命(?![/、])"]},
]

HUA = "禄权科忌"


def layer_sihua(chart: dict) -> set:
    """四层全部合法 (星, 化) 对：生年（标注在星上）∪ 大限 ∪ 流年 ∪ 流月。"""
    pairs = set()
    for p in chart["十二宫"]:
        for s in p["主星"] + p["辅星"]:
            if s["生年四化"]:
                pairs.add((s["名"], s["生年四化"]))
    for layer in ("大限", "流年", "流月"):
        for star, hua in zip(chart[layer]["四化(禄权科忌)"], HUA):
            pairs.add((star, hua))
    return pairs


def build_expect(fx: dict) -> dict:
    chart = build_chart({**fx["birth"], "date": fx["date"], "true_solar": True})
    ming = next(p for p in chart["十二宫"] if p["宫名"] == "命宫")
    body = next(p for p in chart["十二宫"] if p["身宫"])

    must = []
    for s in ming["主星"]:
        must.append({"desc": f"命宫主星{s['名']}",
                     "patterns": [rf"命宫[^。]{{0,15}}{s['名']}",
                                  rf"{s['名']}[^。]{{0,15}}命宫"]})
    if body["宫名"] == "命宫":
        must.append({"desc": "命身同宫",
                     "patterns": ["命身同宫", r"身宫[^。]{0,12}(同宫|命宫)",
                                  r"命宫[^。]{0,12}身宫"]})
    else:
        must.append({"desc": f"身宫落{body['宫名']}",
                     "patterns": [rf"身宫[^。]{{0,12}}{body['宫名']}",
                                  rf"{body['宫名']}[^。]{{0,10}}身宫"]})
    wxj = chart["基本"]["五行局"]
    must.append({"desc": f"五行局{wxj}", "patterns": [wxj]})
    must.append({"desc": "三方四正（三合派纪律锚点）", "patterns": ["三方四正"]})
    for p in chart["十二宫"]:
        for s in p["主星"] + p["辅星"]:
            if s["生年四化"]:
                must.append({"desc": f"生年四化: {s['名']}化{s['生年四化']}",
                             "patterns": [rf"{s['名']}[^。]{{0,8}}{s['生年四化']}"]})
    da = chart["大限"]
    must.append({"desc": f"当前大限{da['宫位']}{da['干支']}",
                 "patterns": [rf"大限[^。]{{0,20}}{da['宫位']}", rf"{da['宫位']}[^。]{{0,10}}大限",
                              rf"大限[^。]{{0,20}}{da['干支']}", da["起讫岁"]]})
    ln = chart["流年"]
    must.append({"desc": f"流年{ln['干支']}",
                 "patterns": [rf"流年[^。]{{0,15}}{ln['干支']}", rf"{ln['干支']}[^。]{{0,10}}流年",
                              rf"20\d\d[^。]{{0,15}}{ln['干支']}"]})

    legit = layer_sihua(chart)
    for star in IMPOSSIBLE_SIHUA:   # 防御性断言：结构性事实若被引擎打破，立即报错
        assert not any(s == star for s, _ in legit), f"{star} 出现四化——引擎行为异常"
    forbidden = [{"desc": f"捉造·不可能四化: {star}化X",
                  "patterns": [rf"{star}[^。]{{0,4}}化(禄|权|科|忌)"]}
                 for star in IMPOSSIBLE_SIHUA] + REDLINES

    return {"reading_type": "ziwei", "must_mention": must,
            "forbidden": forbidden, "must_flag": []}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="紫微评测期望骨架生成器（stdout 输出；本 fixture 零手调，直接重定向提交）。")
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
