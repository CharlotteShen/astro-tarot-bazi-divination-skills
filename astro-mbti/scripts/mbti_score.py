#!/usr/bin/env python3
"""astro-mbti v4.0.0: deterministic MBTI-axis scorer from a natal chart.

A folklore GAME, not a measurement — astrology→MBTI has no scientific
correlation (references/mbti-method.md carries the research). The model never
eyeballs the type: this script owns all arithmetic. Imports build_chart_data
from the natal-astrology skill so real birth data stays in memory (no
intermediate files). Prints to stdout only; never writes files.
"""
import argparse
import json
import os
import sys

AXES = ("EI", "SN", "TF", "JP")
POS = {"EI": "E", "SN": "N", "TF": "T", "JP": "J"}
NEG = {"EI": "I", "SN": "S", "TF": "F", "JP": "P"}

# Static zodiac facts — local copies so scoring stays testable without kerykeion.
ELEMENT = {"Aries": "fire", "Leo": "fire", "Sagittarius": "fire",
           "Taurus": "earth", "Virgo": "earth", "Capricorn": "earth",
           "Gemini": "air", "Libra": "air", "Aquarius": "air",
           "Cancer": "water", "Scorpio": "water", "Pisces": "water"}
MODALITY = {"Aries": "cardinal", "Cancer": "cardinal", "Libra": "cardinal",
            "Capricorn": "cardinal", "Taurus": "fixed", "Leo": "fixed",
            "Scorpio": "fixed", "Aquarius": "fixed", "Gemini": "mutable",
            "Virgo": "mutable", "Sagittarius": "mutable", "Pisces": "mutable"}

# --- v4.0.0 weight table (human-readable mirror with folklore sources:
# references/mbti-method.md; ordered list → deterministic factor order) ---
BODY_W = [("Sun", 2.0), ("Moon", 1.5), ("ASC", 1.5), ("Mercury", 1.0),
          ("Venus", 1.0), ("Mars", 1.0), ("Jupiter", 0.5), ("Saturn", 0.5)]
PERSONAL = ("Sun", "Moon", "Mercury", "Venus", "Mars")
MAJOR_ASPECTS = frozenset({"conjunction", "square", "opposition", "trine"})
ANGULAR_HOUSES = frozenset({1, 4, 7, 10})
E_SUN_HOUSES = frozenset({1, 5, 7, 10, 11})
I_SUN_HOUSES = frozenset({2, 4, 8, 12})
EI_ELEM = {"fire": ("E", 1.0), "air": ("E", 1.0), "earth": ("I", 1.0), "water": ("I", 1.0)}
SN_ELEM = {"earth": ("S", 1.0), "fire": ("N", 1.0), "air": ("N", 0.5), "water": ("S", 0.5)}
TF_ELEM = {"air": ("T", 1.0), "water": ("F", 1.0), "earth": ("T", 0.5), "fire": ("F", 0.5)}
JP_MODE = {"cardinal": ("J", 1.0), "mutable": ("P", 1.0), "fixed": ("J", 0.5)}
ASPECT_UNIT, ASPECT_CAP = 0.75, 1.5
ANGULAR_UNIT, ANGULAR_CAP = 0.5, 2.0
CONF_HIGH, CONF_MEDIUM, NEAR_TIE = 0.5, 0.2, 0.1


def _new_axes():
    return {a: {"factors": [], "net": 0.0, "max": 0.0} for a in AXES}


def _add(axes, axis, label, toward, weight):
    axes[axis]["factors"].append(
        {"factor": label, "toward": toward, "weight": round(weight, 2)})
    axes[axis]["net"] += (1.0 if toward == POS[axis] else -1.0) * weight


def _vote_factors(axes, cd, time_known, moon_ok):
    bodies = {p["body"]: p for p in cd["planets"]}
    for body, w in BODY_W:
        if body == "ASC":
            if not time_known:
                continue
            sign = cd["angles"]["ASC"]["sign"]
        else:
            if body == "Moon" and not moon_ok:
                continue
            sign = bodies[body]["sign"]
        el, mo = ELEMENT[sign], MODALITY[sign]
        for axis, table, key in (("EI", EI_ELEM, el), ("SN", SN_ELEM, el),
                                 ("TF", TF_ELEM, el)):
            toward, mult = table[key]
            _add(axes, axis, f"{body} in {sign} ({key})", toward, w * mult)
        toward, mult = JP_MODE[mo]
        _add(axes, "JP", f"{body} in {sign} ({mo})", toward, w * mult)
    # table max per body = its full weight on every axis (conservative on the
    # split-vote axes — documented in mbti-method.md)
    for body, w in BODY_W:
        if body == "ASC" and not time_known:
            continue
        if body == "Moon" and not moon_ok:
            continue
        for axis in AXES:
            axes[axis]["max"] += w


def _house_factors(axes, cd, time_known, moon_ok):
    if not time_known:
        return
    bodies = {p["body"]: p for p in cd["planets"]}
    pers = [b for b in PERSONAL if moon_ok or b != "Moon"]
    ang = [b for b in pers if bodies[b]["house"] in ANGULAR_HOUSES]
    if ang:
        _add(axes, "EI", "angular personal planets: " + ", ".join(ang), "E",
             min(ANGULAR_UNIT * len(ang), ANGULAR_CAP))
    axes["EI"]["max"] += ANGULAR_CAP
    above = [b for b in pers if bodies[b]["house"] >= 7]
    below = [b for b in pers if bodies[b]["house"] <= 6]
    if len(above) > len(below):
        _add(axes, "EI", f"above-horizon majority ({len(above)}/{len(pers)})", "E", 1.0)
    elif len(below) > len(above):
        _add(axes, "EI", f"below-horizon majority ({len(below)}/{len(pers)})", "I", 1.0)
    axes["EI"]["max"] += 1.0
    sh = bodies["Sun"]["house"]
    if sh in E_SUN_HOUSES:
        _add(axes, "EI", f"Sun in house {sh}", "E", 1.0)
    elif sh in I_SUN_HOUSES:
        _add(axes, "EI", f"Sun in house {sh}", "I", 1.0)
    axes["EI"]["max"] += 1.0
    n_h = [b for b in pers if bodies[b]["house"] in (9, 12)]
    s_h = [b for b in pers if bodies[b]["house"] in (3, 6)]
    if len(n_h) >= 2:
        _add(axes, "SN", "9th/12th-house emphasis: " + ", ".join(n_h), "N", 1.0)
    elif len(s_h) >= 2:
        _add(axes, "SN", "3rd/6th-house emphasis: " + ", ".join(s_h), "S", 1.0)
    axes["SN"]["max"] += 1.0


def _fgroup_factors(axes, cd, time_known, moon_ok):
    bodies = {p["body"]: p for p in cd["planets"]}
    hits = []
    if time_known:
        for b in ("Moon", "Venus"):
            if b == "Moon" and not moon_ok:
                continue
            if bodies[b]["house"] in ANGULAR_HOUSES:
                hits.append(f"{b} angular (house {bodies[b]['house']})")
    mv = {"Venus"} | ({"Moon"} if moon_ok else set())
    for a, _b, t in _major_pairs(cd, mv, {"Mercury"}):
        hits.append(f"{a} {t} Mercury")
    if hits:
        _add(axes, "TF", "Moon/Venus emphasis: " + "; ".join(hits), "F",
             min(ASPECT_UNIT * len(hits), ASPECT_CAP))
    axes["TF"]["max"] += ASPECT_CAP


def _major_pairs(cd, a_set, b_set):
    out = []
    for asp in cd["aspects"]:
        if asp["type"] not in MAJOR_ASPECTS:
            continue
        a, b = asp["a"], asp["b"]
        if a in a_set and b in b_set:
            out.append((a, b, asp["type"]))
        elif b in a_set and a in b_set:
            out.append((b, a, asp["type"]))
    return out


def _aspect_factors(axes, cd, moon_ok):
    lum_merc = {"Sun", "Mercury"} | ({"Moon"} if moon_ok else set())
    lums = {"Sun"} | ({"Moon"} if moon_ok else set())
    hits = _major_pairs(cd, {"Uranus", "Neptune"}, lum_merc)
    if hits:
        _add(axes, "SN", "Uranus/Neptune major aspect to "
             + ", ".join(f"{b} ({a} {t})" for a, b, t in hits), "N",
             min(ASPECT_UNIT * len(hits), ASPECT_CAP))
    axes["SN"]["max"] += ASPECT_CAP
    hits = _major_pairs(cd, {"Saturn"}, lum_merc)
    if hits:
        _add(axes, "TF", "Saturn major aspect to "
             + ", ".join(f"{b} ({t})" for _, b, t in hits), "T",
             min(ASPECT_UNIT * len(hits), ASPECT_CAP))
    axes["TF"]["max"] += ASPECT_CAP
    hits = _major_pairs(cd, {"Saturn"}, lums)
    if hits:
        _add(axes, "JP", "Saturn major aspect to "
             + ", ".join(f"{b} ({t})" for _, b, t in hits), "J", 1.0)
    axes["JP"]["max"] += 1.0
    hits = _major_pairs(cd, {"Jupiter", "Neptune"}, lums)
    if hits:
        _add(axes, "JP", "Jupiter/Neptune major aspect to "
             + ", ".join(f"{b} ({a} {t})" for a, b, t in hits), "P",
             min(ASPECT_UNIT * len(hits), ASPECT_CAP))
    axes["JP"]["max"] += ASPECT_CAP


def _verdicts(axes, time_known):
    out = {}
    for axis in AXES:
        d = axes[axis]
        ratio = abs(d["net"]) / d["max"] if d["max"] else 0.0
        conf = ("high" if ratio >= CONF_HIGH
                else "medium" if ratio >= CONF_MEDIUM else "low")
        capped = (not time_known) and axis in ("EI", "JP") and conf != "low"
        out[axis] = {"net": round(d["net"], 2), "max": round(d["max"], 2),
                     "ratio": round(ratio, 3),
                     "letter": POS[axis] if d["net"] >= 0 else NEG[axis],
                     "confidence": "low" if capped else conf, "capped": capped,
                     "near_tie": abs(d["net"]) < NEAR_TIE * d["max"],
                     "exact_tie": d["net"] == 0.0, "factors": d["factors"]}
    letters = {a: out[a]["letter"] for a in AXES}
    ties = sorted((a for a in AXES if out[a]["near_tie"]),
                  key=lambda a: out[a]["ratio"])
    runner = None
    if ties:
        flip = dict(letters)
        a = ties[0]
        flip[a] = NEG[a] if flip[a] == POS[a] else POS[a]
        runner = "".join(flip[x] for x in AXES)
    return {"axes": out, "type": "".join(letters[a] for a in AXES),
            "runner_up": runner, "near_tie_axes": ties}


def score_chart(cd, time_known=True, moon_ok=True):
    """Deterministic four-axis scoring of a build_chart_data dict."""
    axes = _new_axes()
    _vote_factors(axes, cd, time_known, moon_ok)
    _aspect_factors(axes, cd, moon_ok)
    _fgroup_factors(axes, cd, time_known, moon_ok)
    _house_factors(axes, cd, time_known, moon_ok)
    res = _verdicts(axes, time_known)
    res["time_known"] = time_known
    res["moon_ok"] = moon_ok
    return res


def _moon_sign(cd):
    return next(p["sign"] for p in cd["planets"] if p["body"] == "Moon")


def moon_sign_check(build_chart_data, birth):
    """Unknown birth time: is the Moon's sign stable across the whole day?
    Returns (stable, sign_at_00:00, sign_at_23:59)."""
    s0 = _moon_sign(build_chart_data({**birth, "hour": 0, "minute": 0}))
    s1 = _moon_sign(build_chart_data({**birth, "hour": 23, "minute": 59}))
    return s0 == s1, s0, s1


def read_birth_meta(path):
    """Parse only the first ## Meta block of a birth-data.md (data-contract
    format). Values may carry trailing template comments (`en <!-- en or zh -->`)
    — stripped, so an unfilled template reads as missing fields. time may be
    None (unknown). Raises ValueError on missing required fields."""
    meta, in_meta = {}, False
    with open(path, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s.startswith("## "):
                if in_meta:
                    break              # done with the first Meta block
                in_meta = (s == "## Meta")
                continue
            if in_meta and s.startswith("- ") and ":" in s:
                k, v = s[2:].split(":", 1)
                v = v.split("<!--", 1)[0]   # drop trailing template comments
                meta[k.strip().lower()] = v.strip()
    missing = [k for k in ("date", "lat", "lon", "tz") if not meta.get(k)]
    if missing:
        raise ValueError(
            f"birth-data file {path}: missing Meta field(s): {', '.join(missing)}")
    t = meta.get("time", "")
    return {"name": meta.get("name", ""), "date": meta["date"],
            "time": None if t.lower() in ("", "unknown", "?") else t,
            "lat": float(meta["lat"]), "lon": float(meta["lon"]), "tz": meta["tz"],
            "house_system": meta.get("house_system", "Placidus"),
            "language": meta.get("language", "en")}


# Canonical wording — evals string-match these; never rephrase (mbti-method.md).
DISCLAIMER = {
    "en": ("This is a folklore game, not a measurement. Astrology→MBTI has no "
           "scientific correlation; if this feels accurate, research says that's "
           "self-attribution, not the stars. For your real type, take an actual "
           "MBTI instrument."),
    "zh": ("这是民俗游戏，不是测量。占星→MBTI 没有科学相关性；如果觉得准，研究表明那是"
           "自我归因，不是星星。想知道真实类型，请做正式的 MBTI 测试。"),
}
FOOTNOTE = {
    "en": ("Lineage: MBTI descends from Jung's four functions, which drew on the "
           "classical four elements (air=thinking, water=feeling, earth=sensation, "
           "fire=intuition) — the folklore is coherent, just not predictive "
           "(Carlson 1985; van Rooij 1994; see references/mbti-method.md)."),
    "zh": ("谱系：MBTI 源自荣格四功能，荣格取径古典四元素（风=思考、水=情感、土=感觉、"
           "火=直觉）——民俗自洽，但无预测力（Carlson 1985；van Rooij 1994；"
           "详见 references/mbti-method.md）。"),
}
DEG_TIME = {
    "en": ("Birth time unknown — computed at 12:00; Ascendant, houses and "
           "angularity factors excluded; E/I and J/P confidence capped at low."),
    "zh": "时辰未知——按 12:00 计算；上升、宫位与角宫因子已剔除；E/I 与 J/P 置信度封顶 low。",
}
DEG_MOON = {
    "en": "Moon changed signs that day ({a} → {b}); Moon factors excluded.",
    "zh": "当日月亮换座（{a} → {b}）；月亮因子已剔除。",
}


def render_markdown(res, lang):
    zh = (lang == "zh")
    m = res["meta"]
    t = m["time"] if m["time_known"] else ("时辰未知" if zh else "time unknown")
    lines = ["# MBTI × 本命盘——民俗游戏" if zh else "# MBTI × Natal Chart — folklore game",
             "", f"{m['name']} · {m['date']} · {t}", "",
             "## 逐轴倾向（主体）" if zh else "## Axes (primary content)"]
    for axis in AXES:
        d = res["axes"][axis]
        pair = f"{POS[axis]}/{NEG[axis]}"
        disp = (f"{pair}（完全五五开）" if zh else f"{pair} (exact 50/50)") \
            if d["exact_tie"] else d["letter"]
        conf = d["confidence"] + (
            ("（时辰未知封顶）" if zh else " (capped: time unknown)") if d["capped"] else "")
        lines.append(f"### {pair} — {disp}（置信度：{conf}）" if zh
                     else f"### {pair} — {disp} (confidence: {conf})")
        lines.append(f"净分 {d['net']:+} / 满分 {d['max']}" if zh
                     else f"net {d['net']:+} / max {d['max']}")
        for f in d["factors"]:
            lines.append(f"- {f['factor']} → {f['toward']} ×{f['weight']}")
        lines.append("")
    if res["degraded"]:
        lines.append("## 降级通告" if zh else "## Degradation notice")
        lines.append(DEG_TIME["zh" if zh else "en"])
        moon = res["degraded"]["moon"]
        if moon["dropped"]:
            lines.append(DEG_MOON["zh" if zh else "en"].format(
                a=moon["sign_0000"], b=moon["sign_2359"]))
        lines.append("")
    lines.append("## 你的类型——仅供娱乐" if zh else "## Your type — for fun only")
    tline = f"**{res['type']}**"
    if res["runner_up"]:
        axis = res["near_tie_axes"][0]
        pair = f"{POS[axis]}/{NEG[axis]}"
        tline += (f"——或 {res['runner_up']}（{pair} 接近五五开）" if zh
                  else f" — or {res['runner_up']} ({pair} near 50/50)")
    lines += [tline, "", f"> {DISCLAIMER['zh' if zh else 'en']}", "",
              FOOTNOTE["zh" if zh else "en"], ""]
    return "\n".join(lines)


NATAL_SCRIPTS = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..",
    "natal-astrology", "scripts"))
MISSING_NATAL_MSG = ("astro-mbti requires the natal-astrology skill installed "
                     "alongside (expected its chart engine at {path}). Install "
                     "the full skill set, then retry.")


def load_chart_backend(natal_dir=None):
    path = natal_dir or NATAL_SCRIPTS
    if not os.path.isfile(os.path.join(path, "chart.py")):
        raise RuntimeError(MISSING_NATAL_MSG.format(path=path))
    if path not in sys.path:
        sys.path.insert(0, path)
    from chart import build_chart_data
    return build_chart_data


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="astro-mbti: deterministic MBTI-axis folklore scorer "
                    "(a game, not a measurement). Prints to stdout only.")
    ap.add_argument("--birth-data", help="path to a birth-data.md (reads ## Meta only)")
    ap.add_argument("--date", help="YYYY-MM-DD")
    ap.add_argument("--time", help="HH:MM")
    ap.add_argument("--time-unknown", action="store_true",
                    help="birth time unknown — degraded scoring")
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lon", type=float)
    ap.add_argument("--tz")
    ap.add_argument("--name", default="Chart")
    ap.add_argument("--city", default="")
    ap.add_argument("--house-system", default="Placidus")
    ap.add_argument("--lang", choices=["en", "zh"],
                    help="report language (default: birth-data language field, else en)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    try:
        if args.birth_data:
            if (args.date or args.time or args.lat is not None
                    or args.lon is not None or args.tz):
                print("Error: use either --birth-data or explicit "
                      "--date/--time/--lat/--lon/--tz, not both.", file=sys.stderr)
                return 1
            meta = read_birth_meta(args.birth_data)
        else:
            required = {"--date": args.date, "--lat": args.lat,
                        "--lon": args.lon, "--tz": args.tz}
            missing = [k for k, v in required.items() if v is None]
            if missing:
                print(f"Error: missing {', '.join(missing)} (or pass --birth-data).",
                      file=sys.stderr)
                return 1
            if args.time and args.time_unknown:
                print("Error: --time and --time-unknown are mutually exclusive.",
                      file=sys.stderr)
                return 1
            if not args.time and not args.time_unknown:
                print("Error: pass --time HH:MM or --time-unknown.", file=sys.stderr)
                return 1
            meta = {"name": args.name, "date": args.date,
                    "time": None if args.time_unknown else args.time,
                    "lat": args.lat, "lon": args.lon, "tz": args.tz,
                    "house_system": args.house_system, "language": "en"}
        if args.time_unknown:
            meta["time"] = None
        lang = args.lang or ("zh" if meta.get("language") == "zh" else "en")
        y, mo, d = (int(x) for x in meta["date"].split("-"))
        time_known = meta["time"] is not None
        if time_known:
            hh, mm = (int(x) for x in meta["time"].split(":"))
        else:
            hh, mm = 12, 0
    except (ValueError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    try:
        build = load_chart_backend()
        birth = {"name": meta["name"], "year": y, "month": mo, "day": d,
                 "hour": hh, "minute": mm, "lat": meta["lat"], "lon": meta["lon"],
                 "tz": meta["tz"], "city": args.city,
                 "house_system": meta["house_system"]}
        moon_ok, m0, m1 = True, None, None
        if not time_known:
            moon_ok, m0, m1 = moon_sign_check(build, birth)
        res = score_chart(build(birth), time_known=time_known, moon_ok=moon_ok)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    res["meta"] = {"name": meta["name"], "date": meta["date"], "time": meta["time"],
                   "time_known": time_known, "lang": lang}
    res["degraded"] = None if time_known else {
        "time_unknown": True,
        "dropped": (["ASC votes", "angular/hemisphere/house factors"]
                    + ([] if moon_ok else ["Moon factors"])),
        "moon": {"stable": moon_ok, "sign_0000": m0, "sign_2359": m1,
                 "dropped": not moon_ok}}
    res["disclaimer"] = DISCLAIMER[lang]
    print(json.dumps(res, ensure_ascii=False, indent=2) if args.json
          else render_markdown(res, lang))
    return 0


if __name__ == "__main__":
    sys.exit(main())
