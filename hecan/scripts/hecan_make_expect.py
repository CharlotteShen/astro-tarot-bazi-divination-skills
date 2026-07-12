#!/usr/bin/env python3
"""合参评测期望生成器 — subprocess 跑 hecan_run.py 拿信封（--date 钉死 → ground truth
永久确定），防御断言可用性矩阵后从信封原文提取签名 token 组装 expect。零手调：
committed expect ＝ 本脚本输出逐字节。从不写文件。

用法: python hecan_make_expect.py ../evals/fixtures/hecan-pair.json
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# 既有硬化红线（承 xiuyao 版式：引号/分隔符/否定前缀环视，免责句不误报）
REDLINES = [
    {"desc": "红线: 判死刑词表", "patterns": [
        r"(?<![\"“「『/、不非])绝对不能在一起(?![\"”」』/、])",
        r"(?<![\"“「『/、不非])相性最凶(?![\"”」』/、])",
        r"(?<![\"“「『/、不非])注定(?:破裂|分开)(?![\"”」』/、])"]},
    {"desc": "红线: 灾祸断言", "patterns": [
        r"(?<![/、])血光(?![/、])", r"(?<![/、])破财(?![/、])", r"(?<![/、])病灾(?![/、])"]},
    {"desc": "红线: 打分指数", "patterns": [
        r"相性(?:得分|指数|评分)", r"\d{1,3}\s*分的相性"]},
]


def _grab(pattern: str, text: str, what: str) -> str:
    """信封原文提取一个捕获组；失配时给带上下文的断言消息，而非裸 AttributeError。"""
    m = re.search(pattern, text)
    assert m, f"信封缺少{what}：模式 {pattern!r} 失配"
    return m.group(1)


def run_envelope(fx: dict) -> dict:
    """按 fixture 参数跑编排器一次，返回信封。"""
    cmd = [sys.executable, str(Path(__file__).parent / "hecan_run.py"),
           "--date", fx["date"], "--json"]
    for pre, p in (("--", fx["birth"]["a"]), ("--b-", fx["birth"]["b"])):
        cmd += [f"{pre}year", str(p["year"]), f"{pre}month", str(p["month"]),
                f"{pre}day", str(p["day"]), f"{pre}hour", str(p["hour"]),
                f"{pre}minute", str(p["minute"]), f"{pre}lon", str(p["lon"]),
                f"{pre}lat", str(p["lat"]), f"{pre}tz", p["tz"],
                f"{pre}gender", p["gender"]]
    r = subprocess.run(cmd, capture_output=True, encoding="utf-8", timeout=600)
    if r.returncode != 0:
        raise RuntimeError(f"hecan_run 失败: {(r.stderr or '').strip()[-200:]}")
    return json.loads(r.stdout)


def build_expect(envelope: dict, reading_type: str = "hecan-pair") -> dict:
    sysd = envelope["系统"]
    # 防御断言：可用性矩阵钉死（改 fixture 即报错，防静默产出错误 expect）
    assert sysd["natal"]["状态"] == "degraded", sysd["natal"]["状态"]
    assert sysd["八字"]["状态"] == "ok"
    assert sysd["紫微"]["状态"] == "skipped"
    assert sysd["宿曜"]["状态"] == "ok"
    x = sysd["宿曜"]["输出"]
    ra = _grab(r"甲方看乙方：(\S)（(?:近|中|远)距离", x,
               "甲方看乙方关系（含距离后缀；命/业/胎 无距离会失配）")
    rb = _grab(r"乙方看甲方：(\S)（", x, "乙方看甲方关系")
    assert (ra, rb) == ("成", "危"), (ra, rb)
    xa = _grab(r"【甲方】[^本]*本命宿：(\S)宿", x, "甲方本命宿")
    xb = _grab(r"【乙方】[^本]*本命宿：(\S)宿", x, "乙方本命宿")
    assert (xa, xb) == ("心", "角")
    b = sysd["八字"]["输出"]
    assert "六冲" in b and "五合化土" in b and "七杀" in b
    assert "A.Moon conjunction B.Sun" in sysd["natal"]["输出"]

    must = [
        {"desc": f"甲方本命宿{xa}宿", "patterns": [f"{xa}宿"]},
        {"desc": f"乙方本命宿{xb}宿", "patterns": [f"{xb}宿"]},
        {"desc": f"宿曜方向正确·甲方看乙方＝{ra}", "patterns": [
            f"甲方看乙方[^。]{{0,5}}{ra}", f"{xa}宿看{xb}宿[^。]{{0,5}}{ra}",
            f"(?:乙方|{xb}宿)[^。]{{0,4}}(?:是|为)[^。]{{0,4}}(?:甲方|{xa}宿)的[^。]{{0,3}}{ra}"]},
        {"desc": f"宿曜方向正确·乙方看甲方＝{rb}", "patterns": [
            f"乙方看甲方[^。]{{0,5}}{rb}", f"{xb}宿看{xa}宿[^。]{{0,5}}{rb}",
            f"(?:甲方|{xa}宿)[^。]{{0,4}}(?:是|为)[^。]{{0,4}}(?:乙方|{xb}宿)的[^。]{{0,3}}{rb}"]},
        {"desc": "八字轴真token（六冲/五合化土/七杀/大运 任一）", "patterns": [
            "六冲", "五合化土", "七杀", "大运[^。]{0,10}(同|不同)"]},
        {"desc": "natal轴真token（月日合/日日六合/金火 任一）", "patterns": [
            "月亮[^。]{0,14}太阳", "Moon[^。]{0,25}Sun",
            "太阳[^。]{0,12}太阳", "金星[^。]{0,12}火星", "Venus[^。]{0,22}Mars"]},
        {"desc": "紫微缺席声明", "patterns": [
            "紫微[^。]{0,25}(缺席|跳过|不适用|无双人|未纳入|无法)", "(不含|缺少|少了)[^。]{0,6}紫微"]},
        {"desc": "natal降级声明", "patterns": [
            "(时辰未知|12:00)[^。]{0,30}(宫位|上升)", "宫位[^。]{0,20}不可用", "上升[^。]{0,15}不可用"]},
        {"desc": "共振出现", "patterns": ["共振", "呼应"]},
        {"desc": "分歧出现", "patterns": ["分歧", "各说各话", "张力"]},
    ]
    forbidden = [
        {"desc": "捉造·引用缺席紫微（星曜/宫位正面断言）", "patterns": [
            r"(紫微|天府|贪狼|武曲|廉贞|七杀星|破军|天梁|太阴|巨门)[^。]{0,4}(坐守|入命|守命)",
            r"(命宫|夫妻宫|官禄宫|财帛宫)[^。]{0,8}(主星|坐守)",
            r"(紫微|天府|贪狼|武曲|廉贞|破军|天梁|太阴|巨门)[^。]{0,6}(坐|入|落)[^。]{0,6}宫"]},
        {"desc": "捉造·降级宫位层断言（上升/宫位重叠）", "patterns": [
            r"(上升|Ascendant|ASC)[^。]{0,10}(相位|合相|对分|四分|三合|六合)",
            r"落[^。]{0,5}(对方|B)[^。]{0,5}的?第?[0-9一二三四五六七八九十]+宫",
            r"宫位重叠[^。]{0,10}(显示|表明|说明)"]},
        {"desc": "红线·一致性投票", "patterns": [
            r"(都|一致)[^。]{0,14}(所以|因此|故)[^。]{0,10}(更|必然|肯定)",
            r"(几?[三四多]个?体系|各体系)[^。]{0,8}(印证|投票|背书)"]},
        {"desc": "红线·翻译对照（五行↔元素）", "patterns": [
            r"[木火土金水](?:行)?[^。]{0,4}(对应|等于|就是|即是|＝)[^。]{0,4}[风火土水]象",
            r"五行[^。]{0,6}(对应|映射|翻译)[^。]{0,6}四?元素"]},
        {"desc": "红线·翻译对照（十神↔行星）", "patterns": [
            r"(十神|官杀|七杀|正官|食伤|印星)[^。]{0,4}(就是|等于|即是|＝|对应)[^。]{0,6}(土星|木星|火星|水星|金星|行星|Saturn|Mars)"]},
        {"desc": "红线·多重宿命", "patterns": [
            r"命(更|变)硬", r"(加倍|双重|更加)[^。]{0,4}注定", r"印证[^。]{0,8}(宿命|注定)"]},
        {"desc": f"宿曜方向反转·甲方看乙方≠{rb}", "patterns": [
            f"甲方看乙方[^。]{{0,5}}{rb}", f"{xa}宿看{xb}宿[^。]{{0,5}}{rb}"]},
    ] + REDLINES
    return {"reading_type": reading_type, "must_mention": must,
            "forbidden": forbidden, "must_flag": []}


def build_expect_from_fixture(fx: dict) -> dict:
    return build_expect(run_envelope(fx), fx["reading_type"])


def main(argv=None):
    p = argparse.ArgumentParser(description="合参评测期望生成器（stdout，从不写文件）")
    p.add_argument("fixture", help="fixture JSON 路径")
    args = p.parse_args(argv)
    try:
        fx = json.load(open(args.fixture, encoding="utf-8"))
        out = build_expect_from_fixture(fx)
    except Exception as e:
        print(f"错误：{e}", file=sys.stderr)
        return 1
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
