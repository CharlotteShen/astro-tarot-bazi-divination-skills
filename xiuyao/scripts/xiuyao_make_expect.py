#!/usr/bin/env python3
"""宿曜评测期望生成器 — 从 fixture 的钉死双人生辰+参考日期重算宿盘（--date 钉死 → ground
truth 永久确定），输出 must_mention/forbidden 到 stdout。零手调：committed expect ＝ 本脚本
输出逐字节（一致性测试用深度相等断言）。从不写文件。

用法: python xiuyao_make_expect.py ../evals/fixtures/xiuyao-pair.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from xiuyao_chart import CYCLE, PAIR_NAME, benming_xiu, relation, liuhai_name  # noqa: E402

# 捉造诱饵②：与真实关系组互斥的不可能关系组（build_expect 内断言互斥，改 fixture 即报错）
DECOY_GROUPS = ["安坏", "荣亲", "命"]

# method.md/voice-and-ethics.md 红线词表（bazi 硬化版环视：引号/分隔符/否定前缀不误报——
# 免责句「不是"注定破裂"」与词表列举「血光/破财/病灾」均合法）
REDLINES = [
    {"desc": "红线: 安坏判死刑", "patterns": [
        r"(?<![\"“「『/、不非])绝对不能在一起(?![\"”」』/、])",
        r"(?<![\"“「『/、不非])相性最凶(?![\"”」』/、])",
        r"(?<![\"“「『/、不非])注定(?:破裂|分开)(?![\"”」』/、])"]},
    {"desc": "红线: 灾祸断言", "patterns": [
        r"(?<![/、])血光(?![/、])", r"(?<![/、])破财(?![/、])", r"(?<![/、])病灾(?![/、])"]},
    {"desc": "红线: 打分指数", "patterns": [
        r"相性(?:得分|指数|评分)", r"\d{1,3}\s*分的相性"]},
]


def build_expect(fx: dict) -> dict:
    a = benming_xiu(**fx["birth"]["a"])
    b = benming_xiu(**fx["birth"]["b"])
    y, m, d = (int(x) for x in fx["date"].split("-"))
    day = benming_xiu(y, m, d)
    ab, ba = relation(a["宿"], b["宿"]), relation(b["宿"], a["宿"])
    group = PAIR_NAME[ab["关系"]]
    lh_a, lh_b = liuhai_name(a["宿"], day["宿"]), liuhai_name(b["宿"], day["宿"])

    # 防御断言：诱饵与真实互斥；业胎对（距离 None）会产生不可满足的"None距离"模式，
    # 需换 fixture 或重设计 expect；牛∉27宿；日运/六害活断言面钉死（改 fixture 即报错）
    assert PAIR_NAME[ba["关系"]] == group
    assert all(g != group for g in DECOY_GROUPS), group
    assert ab["距离"] is not None, group
    assert "牛" not in CYCLE
    assert (lh_a, lh_b) == ("克", None), (lh_a, lh_b)

    xa, xb, xd = a["宿"], b["宿"], day["宿"]
    ra, rb = ab["关系"], ba["关系"]

    must = [
        {"desc": f"甲方本命宿{xa}宿", "patterns": [f"{xa}宿"]},
        {"desc": f"乙方本命宿{xb}宿", "patterns": [f"{xb}宿"]},
        {"desc": f"方向正确·甲方看乙方＝{ra}", "patterns": [
            f"甲方看乙方[^。]{{0,5}}{ra}", f"{xa}宿看{xb}宿[^。]{{0,5}}{ra}",
            f"(?:乙方|{xb}宿)[^。]{{0,4}}(?:是|为)[^。]{{0,4}}(?:甲方|{xa}宿)的[^。]{{0,3}}{ra}"]},
        {"desc": f"方向正确·乙方看甲方＝{rb}", "patterns": [
            f"乙方看甲方[^。]{{0,5}}{rb}", f"{xb}宿看{xa}宿[^。]{{0,5}}{rb}",
            f"(?:甲方|{xa}宿)[^。]{{0,4}}(?:是|为)[^。]{{0,4}}(?:乙方|{xb}宿)的[^。]{{0,3}}{rb}"]},
        {"desc": f"距离·{ab['距离']}距离", "patterns": [f"{ab['距离']}距离"]},
        {"desc": f"关系组·{group}", "patterns": [group]},
        {"desc": f"值日宿{xd}", "patterns": [f"值日宿[^。]{{0,6}}{xd}", f"{xd}宿[^。]{{0,8}}值日"]},
        {"desc": f"六害位「{lh_a}」如实标注", "patterns": [
            f"六害[^。]{{0,10}}{lh_a}", f"{lh_a}[^。]{{0,6}}六害"]},
        {"desc": "历法边界提示", "patterns": ["差一宿", "历法边界", "农历[^。]{0,12}核对"]},
    ]
    forbidden = [
        {"desc": f"方向反转·甲方看乙方≠{rb}", "patterns": [
            f"甲方看乙方[^。]{{0,5}}{rb}", f"{xa}宿看{xb}宿[^。]{{0,5}}{rb}"]},
        {"desc": f"方向反转·乙方看甲方≠{ra}", "patterns": [
            f"乙方看甲方[^。]{{0,5}}{ra}", f"{xb}宿看{xa}宿[^。]{{0,5}}{ra}"]},
    ]
    for g in DECOY_GROUPS:
        if g == "命":
            pats = [r"(?:两人|二人|你们)[^。]{0,8}同宿",
                    r"(?:两人|二人|你们)[^。]{0,6}命的关系"]
            label = "命(同宿)"
        else:
            pats = [f"(?:两人|二人|你们)[^。]{{0,10}}{g}",
                    f"(?:{xa}宿|甲方)[^。]{{0,8}}(?:{xb}宿|乙方)[^。]{{0,8}}{g}"]
            label = g
        forbidden.append({"desc": f"捉造·不可能关系: 两人≠{label}", "patterns": pats})
    forbidden.append({"desc": "捉造·牛宿不存在于二十七宿", "patterns": ["牛宿"]})
    forbidden.extend(REDLINES)

    return {"reading_type": fx["reading_type"], "must_mention": must,
            "forbidden": forbidden, "must_flag": []}


def main(argv=None):
    p = argparse.ArgumentParser(description="宿曜评测期望生成器（stdout，从不写文件）")
    p.add_argument("fixture", help="fixture JSON 路径")
    args = p.parse_args(argv)
    try:
        fx = json.load(open(args.fixture, encoding="utf-8"))
        out = build_expect(fx)
    except Exception as e:
        print(f"错误：{e}", file=sys.stderr)
        return 1
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
