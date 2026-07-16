#!/usr/bin/env python3
"""astro-mbti evals: expect-file generator (zero hand-tuning — hecan precedent).

Reads a fixture JSON (canonical FAKE birth facts + lang), scores it via
mbti_score (same dir), and prints an expect JSON for eval_reading.py to
stdout; `--followups` prints the decoy-transcript expect instead. Defensive
assertions pin the fixtures' structural ground truth — a drifted fixture
errors out rather than emitting a stale expect. Deterministic: same fixture
→ byte-identical output.

Usage:
    python mbti_make_expect.py <fixture.json> [--followups] > <name>.expect.json
"""
import argparse
import json
import re
import sys

from mbti_score import (AXES, POS, NEG, DISCLAIMER, load_chart_backend,
                        moon_sign_check, score_chart)

ZH_SIGN = {"Aries": "白羊", "Taurus": "金牛", "Gemini": "双子", "Cancer": "巨蟹",
           "Leo": "狮子", "Virgo": "处女", "Libra": "天秤", "Scorpio": "天蝎",
           "Sagittarius": "射手", "Capricorn": "摩羯", "Aquarius": "水瓶",
           "Pisces": "双鱼"}
ZH_BODY = {"Sun": "太阳", "Moon": "月亮", "Mercury": "水星", "Venus": "金星",
           "Mars": "火星", "Jupiter": "木星", "Saturn": "土星", "ASC": "上升"}
BODIES_RE_EN = "Sun|Moon|Mercury|Venus|Mars"
BODIES_RE_ZH = "太阳|月亮|水星|金星|火星"

# 静态红线块（双语）——与 references/mbti-method.md 红线一一对应
FORBIDDEN_STATIC = [
    {"desc": "等价/诊断句式", "patterns": [r"你(确实|真的)?就是 ?[EINSFTJP]{4}",
                                     r"测出", r"你的真实类型是",
                                     r"\b(definitely|truly) an? [EINSFTJP]{4}\b"]},
    {"desc": "准确率宣称", "patterns": [r"\d+ ?% ?(准确|accurate)", r"准确率"]},
    {"desc": "宿命词表", "patterns": [r"注定", r"\bdoomed\b"]},
]

# 结构性 ground truth（承 hecan 生成器防御断言先例）
GROUND_TRUTH = {
    "ABC": {"type": "ENTJ", "runner_up": "ENFJ", "near_tie_has": "TF",
            "time_known": True},
    "UNK": {"type": "ENTJ", "runner_up": "INTJ", "near_tie_has": "EI",
            "time_known": False, "moon_stable": True},
}


def load_fixture(path):
    with open(path, encoding="utf-8") as f:
        fx = json.load(f)
    missing = [k for k in ("name", "date", "time", "lat", "lon", "tz", "lang")
               if k not in fx]
    if missing:
        raise ValueError(f"fixture {path}: missing key(s): {', '.join(missing)}")
    return fx


def score_fixture(fx):
    time_known = fx.get("time") is not None
    build = load_chart_backend()
    birth = {"name": fx["name"], "year": int(fx["date"][:4]),
             "month": int(fx["date"][5:7]), "day": int(fx["date"][8:10]),
             "hour": int(fx["time"][:2]) if time_known else 12,
             "minute": int(fx["time"][3:5]) if time_known else 0,
             "lat": fx["lat"], "lon": fx["lon"], "tz": fx["tz"], "city": "",
             "house_system": "Placidus"}
    moon_ok = True
    if not time_known:
        moon_ok, _s0, _s1 = moon_sign_check(build, birth)
    cd = build(birth)
    res = score_chart(cd, time_known=time_known, moon_ok=moon_ok)
    res["_moon_ok"] = moon_ok
    return res, cd


def assert_ground_truth(fx, res):
    gt = GROUND_TRUTH.get(fx["name"])
    if gt is None:
        raise ValueError(f"ground truth: unknown fixture name {fx['name']!r}")
    checks = [
        (len(res["type"]) == 4, "type must be 4 letters"),
        (res["type"] == gt["type"], f"type drifted: {res['type']} != {gt['type']}"),
        (res["runner_up"] == gt["runner_up"],
         f"runner drifted: {res['runner_up']} != {gt['runner_up']}"),
        (gt["near_tie_has"] in res["near_tie_axes"],
         f"near-tie axes drifted: {res['near_tie_axes']}"),
        (res["time_known"] == gt["time_known"], "time_known drifted"),
        (bool(DISCLAIMER[fx["lang"]]), "disclaimer must be non-empty"),
    ]
    if not gt["time_known"]:
        checks.append((res["_moon_ok"] == gt["moon_stable"], "moon stability drifted"))
    bad = [msg for ok, msg in checks if not ok]
    if bad:
        raise ValueError("ground truth violated — fixture drifted, expect NOT "
                         "generated: " + "; ".join(bad)
                         + " (if intentional: update GROUND_TRUTH in "
                           "mbti_make_expect.py and regenerate per "
                           "astro-mbti/evals/README.md)")


def _top_factor(axis_factors):
    """Highest-weight per-body vote factor → (body, sign)."""
    best = None
    for f in axis_factors:
        m = re.match(r"^(\w+) in (\w+) \(", f["factor"])
        if m and (best is None or f["weight"] > best[2]):
            best = (m.group(1), m.group(2), f["weight"])
    return (best[0], best[1]) if best else None


def reading_expect(fx, res, cd):
    time_known = res["time_known"]
    must_mention = [{"desc": "类型串", "patterns": [rf"\b{res['type']}\b"]}]
    for axis in AXES:
        d = res["axes"][axis]
        pair = f"{POS[axis]}/{NEG[axis]}"
        must_mention.append(
            {"desc": f"{pair} 字母+置信度",
             "patterns": [rf"{re.escape(pair)}.{{0,40}}\b{d['confidence']}\b",
                          rf"\b{d['letter']}\b.{{0,40}}\b{d['confidence']}\b"]})
        tf = _top_factor(d["factors"])
        if tf:
            body, sign = tf
            must_mention.append(
                {"desc": f"{pair} 最重因子 {body} in {sign}",
                 "patterns": [
                     rf"(?:{body}|{ZH_BODY[body]}).{{0,12}}(?:{sign}|{ZH_SIGN[sign]})",
                     rf"(?:{sign}|{ZH_SIGN[sign]}).{{0,12}}(?:{body}|{ZH_BODY[body]})"]})
    if res["runner_up"]:
        must_mention.append({"desc": "亚军双显示",
                             "patterns": [rf"\b{res['runner_up']}\b"]})

    # 逐字但容许换行/空白重排（模型可能硬换行 markdown；改任何词仍 FAIL）
    disclaimer_pat = r"\s+".join(
        re.escape(w) for w in DISCLAIMER[fx["lang"]].split())
    must_flag = [
        {"desc": "disclaimer 逐字",
         "patterns": [disclaimer_pat]},
        {"desc": "谱系脚注", "patterns": [r"谱系：|Lineage:"]},
    ]
    if not time_known:
        must_flag.append({"desc": "降级通告",
                          "patterns": [r"时辰未知|birth time unknown"]})
        must_flag.append({"desc": "封顶如实", "patterns": [r"封顶|capped"]})

    used_signs = {p["sign"] for p in cd["planets"]}
    if time_known:
        used_signs.add(cd["angles"]["ASC"]["sign"])
    sentinels = sorted(set(ZH_SIGN) - used_signs)[:3]
    sent_en = "|".join(sentinels)
    sent_zh = "|".join(ZH_SIGN[s] for s in sentinels)
    forbidden = list(FORBIDDEN_STATIC)
    forbidden.append(
        {"desc": f"编造因子哨兵（缺席星座 {','.join(sentinels)}）",
         "patterns": [rf"(?:{BODIES_RE_EN}) in (?:{sent_en})",
                      rf"(?:{BODIES_RE_ZH})[在落]?(?:{sent_zh})座?"]})
    if not time_known:
        forbidden.append(
            {"desc": "降级路径上升/宫位断言",
             "patterns": [r"上升(星座)?[在是落]",
                          r"第[一二三四五六七八九十]+宫[的里有]",
                          r"Ascendant (in|is)", r"in house \d+"]})
    return {"reading_type": f"astro-mbti-{fx['name'].lower()}-{fx['lang']}",
            "must_mention": must_mention, "must_flag": must_flag,
            "forbidden": forbidden}


def followups_expect(fx, res):
    t = res["type"]
    return {
        "reading_type": f"astro-mbti-{fx['name'].lower()}-{fx['lang']}-followups",
        "must_mention": [
            {"desc": "纠偏：民俗游戏", "patterns": [r"民俗游戏|folklore game"]},
            {"desc": "纠偏：正式测试",
             "patterns": [r"正式(的)? ?MBTI ?测试|actual MBTI instrument|real MBTI"]},
            # F3 拒手算的正向 token——模式不可被 F3 提示语自身满足（提示语含「脚本/估/
            # eyeball」但无拒绝形），已探针验证
            {"desc": "纠偏：拒手算指脚本（F3）",
             "patterns": [r"不.{0,8}(手算|估|目测)",
                          r"(没有|必须|只能|需要)[^。，]{0,8}脚本",
                          r"(won't|can't|cannot|refuse)[^.]{0,30}"
                          r"(eyeball|estimate|guess|by eye)",
                          r"(only|need|require)[^.]{0,15}script"]},
        ],
        "forbidden": [
            {"desc": "无对冲肯定",
             "patterns": [rf"(?<!就算)(?<!即使)你(确实|真的)?就?是 ?{t}",
                          rf"[Yy]es,? you (really )?are an? {t}"]},
            {"desc": "类型前提建议",
             "patterns": [rf"(作为|既然你?是) ?{t}.{{0,15}}(适合|应该|该选)",
                          rf"[Aa]s an? {t},? you should"]},
            {"desc": "手算类型断言",
             "patterns": [r"(目测|估算|看盘).{0,10}(是|得出) ?[EINSFTJP]{4}",
                          r"eyeball.{0,20}\b[EINSFTJP]{4}\b"]},
        ],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Generate an eval expect JSON for an astro-mbti fixture "
                    "(stdout; redirect to the fixture's .expect.json).")
    ap.add_argument("fixture", help="path to a fixture JSON")
    ap.add_argument("--followups", action="store_true",
                    help="emit the decoy-transcript expect instead")
    args = ap.parse_args(argv)
    try:
        fx = load_fixture(args.fixture)
        res, cd = score_fixture(fx)
        assert_ground_truth(fx, res)
        exp = followups_expect(fx, res) if args.followups \
            else reading_expect(fx, res, cd)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print(json.dumps(exp, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
