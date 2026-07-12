"""Route A synastry: inter-aspects + house overlays + midpoint composite from two births.

Reuses helpers/constants from chart.py. Input is two birth dicts (same shape as chart.build_chart_data).
CLI: pass a JSON payload {"birth_a":{...},"birth_b":{...},"relationship_type":"romantic"} on stdin.
"""
import argparse
import json
import sys

from chart import (SIGNS, HOUSE_NUM, HOUSE_CODE, _full_sign, _abs_pos, _point)

PLANET_ATTRS = [
    ("Sun", "sun"), ("Moon", "moon"), ("Mercury", "mercury"), ("Venus", "venus"),
    ("Mars", "mars"), ("Jupiter", "jupiter"), ("Saturn", "saturn"),
    ("Uranus", "uranus"), ("Neptune", "neptune"), ("Pluto", "pluto"),
]
POINT_ATTRS = [("North Node", "true_node"), ("Chiron", "chiron")]
CUSP_ATTRS = ["first_house", "second_house", "third_house", "fourth_house", "fifth_house",
              "sixth_house", "seventh_house", "eighth_house", "ninth_house", "tenth_house",
              "eleventh_house", "twelfth_house"]
ASPECT_DEFS = [("conjunction", 0, 8), ("sextile", 60, 6), ("square", 90, 8),
               ("trine", 120, 8), ("opposition", 180, 8)]
CROSS_BODIES = [n for n, _ in PLANET_ATTRS] + ["North Node", "Chiron", "ASC", "MC"]
PLANET_NAMES = [n for n, _ in PLANET_ATTRS]


def midpoint(a: float, b: float) -> float:
    # NOTE: at an exact 180° opposition both arcs are equal, so the result is order-dependent
    # (midpoint(0,180)=270 but midpoint(180,0)=90). Inherent to nearer-arc midpoint; acceptable.
    diff = ((b - a + 540) % 360) - 180
    return (a + diff / 2) % 360


def _aspect(separation: float):
    s = separation % 360
    if s > 180:
        s = 360 - s
    for atype, angle, orb in ASPECT_DEFS:
        if abs(s - angle) <= orb:
            return atype, round(abs(s - angle), 2)
    return None


def find_house(abs_pos: float, cusps: list) -> int:
    for i in range(12):
        start = cusps[i]
        end = cusps[(i + 1) % 12]
        span = (end - start) % 360
        off = (abs_pos - start) % 360
        if span == 0 or off < span:
            return i + 1
    return 12


def _subject(birth: dict):
    from kerykeion import AstrologicalSubject
    hs = HOUSE_CODE.get(birth.get("house_system", "Placidus"))
    if hs is None:
        raise ValueError(f"Unsupported house_system {birth.get('house_system')!r}. "
                         f"Supported: {sorted(HOUSE_CODE)}")
    return AstrologicalSubject(
        birth.get("name", "Chart"), birth["year"], birth["month"], birth["day"],
        birth["hour"], birth["minute"], lng=birth["lon"], lat=birth["lat"],
        tz_str=birth["tz"], city=birth.get("city", ""), houses_system_identifier=hs)


def _person(birth: dict) -> dict:
    subj = _subject(birth)
    bodies = {}
    for name, attr in PLANET_ATTRS + POINT_ATTRS:
        p = getattr(subj, attr, None)
        if p is None:
            continue
        sign = p.sign if p.sign in SIGNS else _full_sign(p.sign)
        bodies[name] = {"sign": sign, "degree": round(float(p.position), 2),
                        "house": HOUSE_NUM.get(p.house, 0), "retro": bool(p.retrograde),
                        "abs": _abs_pos(p)}
    asc, mc = subj.first_house, subj.tenth_house
    bodies["ASC"] = {**_point(asc), "house": 1, "retro": False, "abs": _abs_pos(asc)}
    bodies["MC"] = {**_point(mc), "house": 10, "retro": False, "abs": _abs_pos(mc)}
    cusps = [_abs_pos(getattr(subj, a)) for a in CUSP_ATTRS]
    return {"bodies": bodies, "cusps": cusps}


def _export_person(birth: dict, person: dict) -> dict:
    b = person["bodies"]
    return {
        "meta": {"name": birth.get("name", ""),
                 "date": f"{birth['year']:04d}-{birth['month']:02d}-{birth['day']:02d}",
                 "time": f"{birth['hour']:02d}:{birth['minute']:02d}",
                 "location": birth.get("city", "")},
        "planets": [{"body": n, "sign": b[n]["sign"], "degree": b[n]["degree"],
                     "house": b[n]["house"], "retrograde": b[n]["retro"]} for n in PLANET_NAMES],
        "angles": {"ASC": {"sign": b["ASC"]["sign"], "degree": b["ASC"]["degree"]},
                   "MC": {"sign": b["MC"]["sign"], "degree": b["MC"]["degree"]}},
        "points": [{"body": n, "sign": b[n]["sign"], "degree": b[n]["degree"],
                    "house": b[n]["house"], "retrograde": b[n]["retro"]}
                   for n in ("North Node", "Chiron") if n in b],
        "cusps": [round(c, 2) for c in person["cusps"]],
    }


def find_reinforced(inter_aspects: list) -> dict:
    """Derive reinforced contacts from synastry inter-aspects (prefix-agnostic on the body labels).

    double_whammies: reciprocal body-type pairs {P, Q} (P != Q) where both `<x>.P–<y>.Q` and
                     `<x>.Q–<y>.P` aspects exist.
    focal_points:    any body label appearing in >= 2 inter-aspects (a hotspot), sorted by count desc.
    """
    directed = {}   # (P, Q) -> the inter-aspect entry whose `a` body is P and `b` body is Q
    for x in inter_aspects:
        p = x["a"].split(".", 1)[1]
        q = x["b"].split(".", 1)[1]
        directed[(p, q)] = x
    double_whammies, seen = [], set()
    for (p, q) in directed:
        if p != q and (q, p) in directed:
            key = frozenset((p, q))
            if key not in seen:
                seen.add(key)
                double_whammies.append({"pair": sorted([p, q]),
                                        "aspects": [directed[(p, q)], directed[(q, p)]]})
    counts = {}
    for x in inter_aspects:
        counts.setdefault(x["a"], []).append(x)
        counts.setdefault(x["b"], []).append(x)
    focal_points = sorted(
        [{"body": lbl, "count": len(v), "aspects": v} for lbl, v in counts.items() if len(v) >= 2],
        key=lambda f: -f["count"])
    return {"double_whammies": double_whammies, "focal_points": focal_points}


def build_synastry_data(birth_a: dict, birth_b: dict, relationship_type: str = "romantic") -> dict:
    A, B = _person(birth_a), _person(birth_b)

    inter = []
    for an in CROSS_BODIES:
        if an not in A["bodies"]:
            continue
        for bn in CROSS_BODIES:
            if bn not in B["bodies"]:
                continue
            res = _aspect(A["bodies"][an]["abs"] - B["bodies"][bn]["abs"])
            if res:
                inter.append({"a": f"A.{an}", "type": res[0], "b": f"B.{bn}", "orb": res[1]})

    overlays = {"a_in_b": [], "b_in_a": []}
    for n in PLANET_NAMES:
        overlays["a_in_b"].append({"planet": f"A.{n}", "house": find_house(A["bodies"][n]["abs"], B["cusps"])})
        overlays["b_in_a"].append({"planet": f"B.{n}", "house": find_house(B["bodies"][n]["abs"], A["cusps"])})

    asc_c = midpoint(A["bodies"]["ASC"]["abs"], B["bodies"]["ASC"]["abs"])
    mc_c = midpoint(A["bodies"]["MC"]["abs"], B["bodies"]["MC"]["abs"])
    asc_sign_idx = int(asc_c // 30)
    comp_abs, comp_planets = {}, []
    for n in PLANET_NAMES:
        m = midpoint(A["bodies"][n]["abs"], B["bodies"][n]["abs"])
        comp_abs[n] = m
        sign_idx = int(m // 30)
        comp_planets.append({"body": n, "sign": SIGNS[sign_idx], "degree": round(m % 30, 2),
                             "house": ((sign_idx - asc_sign_idx) % 12) + 1})
    comp_aspects = []
    names = list(comp_abs)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            res = _aspect(comp_abs[names[i]] - comp_abs[names[j]])
            if res:
                comp_aspects.append({"a": names[i], "type": res[0], "b": names[j], "orb": res[1]})
    composite = {"planets": comp_planets,
                 "angles": {"ASC": {"sign": SIGNS[asc_sign_idx], "degree": round(asc_c % 30, 2)},
                            "MC": {"sign": SIGNS[int(mc_c // 30)], "degree": round(mc_c % 30, 2)}},
                 "aspects": comp_aspects}

    reinforced = find_reinforced(inter)
    return {"relationship_type": relationship_type,
            "person_a": _export_person(birth_a, A), "person_b": _export_person(birth_b, B),
            "inter_aspects": inter,
            "double_whammies": reinforced["double_whammies"],
            "focal_points": reinforced["focal_points"],
            "overlays": overlays, "composite": composite}


def render_markdown(sd: dict) -> str:
    lines = ["# Synastry", "", f"relationship_type: {sd['relationship_type']}", "",
             "## Inter-aspects"]
    for a in sd["inter_aspects"]:
        lines.append(f"- {a['a']} {a['type']} {a['b']} ({a['orb']})")
    lines += ["", "## Overlays — A's planets in B's houses"]
    for o in sd["overlays"]["a_in_b"]:
        lines.append(f"- {o['planet']} in B house {o['house']}")
    lines += ["", "## Overlays — B's planets in A's houses"]
    for o in sd["overlays"]["b_in_a"]:
        lines.append(f"- {o['planet']} in A house {o['house']}")
    c = sd["composite"]
    lines += ["", "## Composite",
              f"- ASC: {c['angles']['ASC']['sign']} {c['angles']['ASC']['degree']}",
              f"- MC: {c['angles']['MC']['sign']} {c['angles']['MC']['degree']}"]
    for p in c["planets"]:
        lines.append(f"- {p['body']}: {p['sign']} {p['degree']} (house {p['house']})")
    lines.append("")
    for a in c["aspects"]:
        lines.append(f"- composite {a['a']} {a['type']} {a['b']} ({a['orb']})")
    lines.append("")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Compute synastry data from two births (JSON on stdin).")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    try:
        payload = json.load(sys.stdin)
        sd = build_synastry_data(payload["birth_a"], payload["birth_b"],
                                 payload.get("relationship_type", "romantic"))
    except Exception as e:  # noqa: BLE001 — surface a clean message, no traceback
        print(f"Error: {e}", file=sys.stderr)
        return 1
    out = json.dumps(sd, ensure_ascii=False, indent=2) if args.json else render_markdown(sd)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"Wrote {args.out}. Keep birth data private.")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
