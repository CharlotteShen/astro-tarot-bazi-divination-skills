"""Route A: generate a birth-data file from birth details using kerykeion (Swiss Ephemeris).

Usage:
    python chart.py --name "You" --date 1990-06-15 --time 12:00 \
        --lat 31.23 --lon 121.47 --tz Asia/Shanghai --city Shanghai \
        [--house-system Placidus] [--out birth-data.md]
"""
import argparse
import json
import sys

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
ELEMENT = {s: e for s, e in zip(
    SIGNS,
    ["fire", "earth", "air", "water"] * 3)}
MODALITY = {s: m for s, m in zip(
    SIGNS,
    (["cardinal", "fixed", "mutable"] * 4))}
HOUSE_NUM = {
    "First_House": 1, "Second_House": 2, "Third_House": 3, "Fourth_House": 4,
    "Fifth_House": 5, "Sixth_House": 6, "Seventh_House": 7, "Eighth_House": 8,
    "Ninth_House": 9, "Tenth_House": 10, "Eleventh_House": 11, "Twelfth_House": 12,
}
HOUSE_CODE = {"Placidus": "P", "Whole Sign": "W", "Koch": "K", "Equal": "A"}
PLANET_ATTRS = [
    ("Sun", "sun"), ("Moon", "moon"), ("Mercury", "mercury"), ("Venus", "venus"),
    ("Mars", "mars"), ("Jupiter", "jupiter"), ("Saturn", "saturn"),
    ("Uranus", "uranus"), ("Neptune", "neptune"), ("Pluto", "pluto"),
]
ASPECT_DEFS = [
    ("conjunction", 0, 8), ("sextile", 60, 6), ("square", 90, 8),
    ("trine", 120, 8), ("opposition", 180, 8),
]

import swisseph as swe  # noqa: E402  (declination + vertex)

# --- v1.1.3 enrichment tuning (own conventions — adjust freely) ---
MIDPOINT_ORB = 1.5   # ° — a planet "occupies" a two-planet midpoint within this orb
PARALLEL_ORB = 1.0   # ° — declination parallel / contra-parallel orb
SWE_BODY = {"Sun": 0, "Moon": 1, "Mercury": 2, "Venus": 3, "Mars": 4, "Jupiter": 5,
            "Saturn": 6, "Uranus": 7, "Neptune": 8, "Pluto": 9, "North Node": 11, "Chiron": 15}
CUSP_ATTRS = ["first_house", "second_house", "third_house", "fourth_house", "fifth_house",
              "sixth_house", "seventh_house", "eighth_house", "ninth_house", "tenth_house",
              "eleventh_house", "twelfth_house"]

# --- v1.2.2 asteroid + Black Moon Lilith enrichment (own conventions — adjust freely) ---
ASTEROID_SWE = {"Ceres": 17, "Pallas": 18, "Juno": 19, "Vesta": 20, "Black Moon Lilith": 12}
ASTEROID_ORB = 2.0   # ° — tight contact orb for asteroids/Lilith to natal planets + angles


def _midpoint(a, b):
    diff = ((b - a + 540) % 360) - 180
    return (a + diff / 2) % 360


def _ang_dist(a, b):
    d = abs(a - b) % 360
    return d if d <= 180 else 360 - d


def find_house(abs_pos, cusps):
    for i in range(12):
        start, end = cusps[i], cusps[(i + 1) % 12]
        span = (end - start) % 360
        if span == 0 or (abs_pos - start) % 360 < span:
            return i + 1
    return 12


def _full_sign(sign):
    # kerykeion may return 2-letter sign codes; map them.
    codes = {"Ari": "Aries", "Tau": "Taurus", "Gem": "Gemini", "Can": "Cancer",
             "Leo": "Leo", "Vir": "Virgo", "Lib": "Libra", "Sco": "Scorpio",
             "Sag": "Sagittarius", "Cap": "Capricorn", "Aqu": "Aquarius", "Pis": "Pisces"}
    return codes.get(sign, sign)


def _abs_pos(point):
    if hasattr(point, "abs_pos") and point.abs_pos is not None:
        return float(point.abs_pos)
    sign = point.sign if point.sign in SIGNS else _full_sign(point.sign)
    return SIGNS.index(sign) * 30 + float(point.position)


def _point(point):
    sign = point.sign if point.sign in SIGNS else _full_sign(point.sign)
    return {"sign": sign, "degree": round(float(point.position), 2)}


def _enrichment(subj, abs_positions, cusps, lat, lon, hs_code):
    asc, sun, moon, ven = (abs_positions["ASC"], abs_positions["Sun"],
                           abs_positions["Moon"], abs_positions["Venus"])
    sect = "day" if find_house(sun, cusps) in (7, 8, 9, 10, 11, 12) else "night"

    def place(longitude):
        x = longitude % 360
        return {"sign": SIGNS[int(x // 30)], "degree": round(x % 30, 2), "house": find_house(x, cusps)}

    if sect == "day":
        fortune, spirit = asc + moon - sun, asc + sun - moon
        eros = asc + ven - spirit
    else:
        fortune, spirit = asc + sun - moon, asc + moon - sun
        eros = asc + spirit - ven
    lots = {"fortune": place(fortune), "spirit": place(spirit), "eros": place(eros)}

    planet_abs = {n: abs_positions[n] for n, _ in PLANET_ATTRS}
    midpoints = {"sun_moon": place(_midpoint(sun, moon)), "occupied": []}
    names = list(planet_abs)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            m = _midpoint(planet_abs[names[i]], planet_abs[names[j]])
            for r in names:
                if r in (names[i], names[j]):
                    continue
                d = _ang_dist(planet_abs[r], m)
                if d <= MIDPOINT_ORB:
                    midpoints["occupied"].append(
                        {"planet": r, "of": sorted([names[i], names[j]]), "orb": round(d, 2)})

    jd = subj.julian_day
    decl = {}
    for name, bid in SWE_BODY.items():
        try:
            xx, _flag = swe.calc_ut(jd, bid, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)
            decl[name] = round(xx[1], 2)
        except Exception:  # noqa: BLE001 — body unavailable (e.g. missing asteroid ephemeris); skip
            pass
    parallels = []
    dn = [n for n, _ in PLANET_ATTRS if n in decl]
    for i in range(len(dn)):
        for j in range(i + 1, len(dn)):
            a, b = decl[dn[i]], decl[dn[j]]
            if abs(a - b) <= PARALLEL_ORB:
                parallels.append({"a": dn[i], "b": dn[j], "type": "parallel", "orb": round(abs(a - b), 2)})
            elif abs(a + b) <= PARALLEL_ORB:
                parallels.append({"a": dn[i], "b": dn[j], "type": "contra_parallel", "orb": round(abs(a + b), 2)})

    try:
        _c, ascmc = swe.houses_ex(jd, lat, lon, hs_code.encode())
        vertex = place(ascmc[3])
    except Exception:  # noqa: BLE001
        vertex = None

    ast_pos = {}
    for name, bid in ASTEROID_SWE.items():
        try:
            xx, _flag = swe.calc_ut(jd, bid, swe.FLG_SWIEPH)
            ast_pos[name] = xx[0] % 360
        except Exception:  # noqa: BLE001 — body unavailable; skip
            pass
    asteroids = {n.lower(): place(ast_pos[n]) for n in ("Ceres", "Pallas", "Juno", "Vesta")
                 if n in ast_pos}
    black_moon_lilith = place(ast_pos["Black Moon Lilith"]) if "Black Moon Lilith" in ast_pos else None

    asteroid_contacts = []
    ast_targets = [n for n, _ in PLANET_ATTRS] + ["ASC", "MC"]
    for aname, alon in ast_pos.items():
        for tname in ast_targets:
            sep = _ang_dist(alon, abs_positions[tname])
            for atype, angle, _orb in ASPECT_DEFS:
                if abs(sep - angle) <= ASTEROID_ORB:
                    asteroid_contacts.append(
                        {"a": aname, "type": atype, "b": tname, "orb": round(abs(sep - angle), 2)})
                    break

    return {"sect": sect, "lots": lots, "midpoints": midpoints,
            "declinations": decl, "parallels": parallels, "vertex": vertex,
            "asteroids": asteroids, "black_moon_lilith": black_moon_lilith,
            "asteroid_contacts": asteroid_contacts}


def _house_code(birth: dict) -> str:
    hs_name = birth.get("house_system") or "Placidus"
    if hs_name not in HOUSE_CODE:
        raise ValueError(
            f"Unsupported house_system {hs_name!r}. Supported: {sorted(HOUSE_CODE)}")
    return HOUSE_CODE[hs_name]


def _subject(birth: dict):
    from kerykeion import AstrologicalSubject
    return AstrologicalSubject(
        birth.get("name", "Chart"),
        birth["year"], birth["month"], birth["day"], birth["hour"], birth["minute"],
        lng=birth["lon"], lat=birth["lat"], tz_str=birth["tz"],
        city=birth.get("city", ""), houses_system_identifier=_house_code(birth),
    )


def build_chart_data(birth: dict) -> dict:
    hs = _house_code(birth)
    subj = _subject(birth)

    planets = []
    abs_positions = {}
    elements = {"fire": 0, "earth": 0, "air": 0, "water": 0}
    modalities = {"cardinal": 0, "fixed": 0, "mutable": 0}
    for name, attr in PLANET_ATTRS:
        p = getattr(subj, attr)
        sign = p.sign if p.sign in SIGNS else _full_sign(p.sign)
        planets.append({
            "body": name, "sign": sign, "degree": round(float(p.position), 2),
            "house": HOUSE_NUM.get(p.house, 0), "retrograde": bool(p.retrograde),
        })
        abs_positions[name] = _abs_pos(p)
        elements[ELEMENT[sign]] += 1
        modalities[MODALITY[sign]] += 1

    points = []
    for name, attr in [("North Node", "true_node"), ("Chiron", "chiron")]:
        p = getattr(subj, attr, None)
        if p is None:
            continue
        sign = p.sign if p.sign in SIGNS else _full_sign(p.sign)
        points.append({
            "body": name, "sign": sign, "degree": round(float(p.position), 2),
            "house": HOUSE_NUM.get(p.house, 0), "retrograde": bool(p.retrograde),
        })
        abs_positions[name] = _abs_pos(p)

    asc, mc = subj.first_house, subj.tenth_house
    abs_positions["ASC"] = _abs_pos(asc)
    abs_positions["MC"] = _abs_pos(mc)

    aspects = []
    items = list(abs_positions.items())
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, pa = items[i]
            b, pb = items[j]
            sep = abs(pa - pb) % 360
            if sep > 180:
                sep = 360 - sep
            for atype, angle, orb in ASPECT_DEFS:
                if abs(sep - angle) <= orb:
                    aspects.append({"a": a, "type": atype, "b": b,
                                    "orb": round(abs(sep - angle), 2)})
                    break

    cusps = [_abs_pos(getattr(subj, a)) for a in CUSP_ATTRS]
    enrichment = _enrichment(subj, abs_positions, cusps, birth["lat"], birth["lon"], hs)
    return {
        "meta": {
            "name": birth.get("name", ""),
            "date": f"{birth['year']:04d}-{birth['month']:02d}-{birth['day']:02d}",
            "time": f"{birth['hour']:02d}:{birth['minute']:02d}",
            "location": birth.get("city", ""), "lat": birth["lat"], "lon": birth["lon"],
            "tz": birth["tz"], "house_system": birth.get("house_system") or "Placidus",
            "zodiac": "tropical", "source": "kerykeion", "language": "en",
        },
        "planets": planets,
        "angles": {"ASC": _point(asc), "MC": _point(mc)},
        "points": points,
        "aspects": aspects,
        "balance": {"elements": elements, "modalities": modalities},
        "enrichment": enrichment,
    }


def render_markdown(cd: dict) -> str:
    m = cd["meta"]
    lines = ["# Birth Data", "", "## Meta"]
    for k in ["name", "date", "time", "location", "lat", "lon", "tz",
              "house_system", "zodiac", "source", "language"]:
        lines.append(f"- {k}: {m[k]}")
    lines += ["", "## Planets"]
    for p in cd["planets"]:
        lines.append(f"- {p['body']}: sign={p['sign']} degree={p['degree']} "
                     f"house={p['house']} retrograde={'yes' if p['retrograde'] else 'no'}")
    lines += ["", "## Angles",
              f"- ASC: sign={cd['angles']['ASC']['sign']} degree={cd['angles']['ASC']['degree']}",
              f"- MC: sign={cd['angles']['MC']['sign']} degree={cd['angles']['MC']['degree']}",
              "", "## Points"]
    for p in cd["points"]:
        lines.append(f"- {p['body']}: sign={p['sign']} degree={p['degree']} "
                     f"house={p['house']} retrograde={'yes' if p['retrograde'] else 'no'}")
    lines += ["", "## Aspects"]
    for a in cd["aspects"]:
        lines.append(f"- {a['a']} {a['type']} {a['b']} ({a['orb']})")
    b = cd["balance"]
    lines += ["", "## Balance",
              f"- elements: fire={b['elements']['fire']} earth={b['elements']['earth']} "
              f"air={b['elements']['air']} water={b['elements']['water']}",
              f"- modalities: cardinal={b['modalities']['cardinal']} "
              f"fixed={b['modalities']['fixed']} mutable={b['modalities']['mutable']}", ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Generate a birth-data file via kerykeion.")
    ap.add_argument("--name", default="Chart")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--time", required=True, help="HH:MM")
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--tz", required=True)
    ap.add_argument("--city", default="")
    ap.add_argument("--house-system", default="Placidus")
    ap.add_argument("--out", default="birth-data.md")
    ap.add_argument("--json", action="store_true", help="write JSON instead of Markdown")
    args = ap.parse_args(argv)

    try:
        y, mo, d = (int(x) for x in args.date.split("-"))
        hh, mm = (int(x) for x in args.time.split(":"))
    except ValueError:
        print(f"Error: invalid --date {args.date!r} or --time {args.time!r}; "
              f"expected YYYY-MM-DD and HH:MM.", file=sys.stderr)
        return 1
    birth = {"name": args.name, "year": y, "month": mo, "day": d, "hour": hh, "minute": mm,
             "lat": args.lat, "lon": args.lon, "tz": args.tz, "city": args.city,
             "house_system": args.house_system}
    try:
        cd = build_chart_data(birth)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    out_path = args.out
    if args.json and args.out == "birth-data.md":
        out_path = "birth-data.json"
    out = json.dumps(cd, ensure_ascii=False, indent=2) if args.json else render_markdown(cd)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"Wrote {out_path} (source=kerykeion). Keep it private; it is gitignored.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
