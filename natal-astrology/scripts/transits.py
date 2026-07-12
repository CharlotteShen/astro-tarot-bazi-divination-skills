"""Route A transit snapshot: which transiting bodies aspect the natal chart on a given date,
each with orb and applying/separating. Reuses chart.py + sensitivity.py. Snapshot only — exact
perfection dates and retrograde passes are a later version (v1.2.1). Never forecasting.
"""
import argparse
import sys
from datetime import date, timedelta

from chart import build_chart_data
from sensitivity import _abs

# --- v1.2.0 transit tuning (own conventions — tighter than the rest of the skill) ---
TRANSIT_ASPECTS = [("conjunction", 0, 3), ("sextile", 60, 2), ("square", 90, 3),
                   ("trine", 120, 3), ("opposition", 180, 3)]
MOON_ORB_BONUS = 2.0   # the transiting Moon sweeps ~13°/day — allow a wider orb for it

MOVERS = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
          "Uranus", "Neptune", "Pluto", "Chiron", "North Node"]
SLOW_MOVERS = {"Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Chiron", "North Node"}
ANGLE_OF = {atype: angle for atype, angle, _orb in TRANSIT_ASPECTS}


def _positions(on_date: str, lat, lon, tz, house_system="Placidus") -> dict:
    y, mo, d = (int(x) for x in on_date.split("-"))
    cd = build_chart_data({"name": "transit", "year": y, "month": mo, "day": d,
                           "hour": 12, "minute": 0, "lat": lat, "lon": lon, "tz": tz,
                           "city": "", "house_system": house_system})
    pos = {p["body"]: _abs(p["sign"], p["degree"]) for p in cd["planets"]}
    for p in cd["points"]:
        if p["body"] in ("Chiron", "North Node"):
            pos[p["body"]] = _abs(p["sign"], p["degree"])
    return pos


def _aspect_between(a_abs: float, b_abs: float, is_moon: bool):
    sep = abs(a_abs - b_abs) % 360
    if sep > 180:
        sep = 360 - sep
    for atype, angle, orb in TRANSIT_ASPECTS:
        allowed = orb + (MOON_ORB_BONUS if is_moon else 0)
        if abs(sep - angle) <= allowed:
            return (atype, round(abs(sep - angle), 2))
    return None


def _orb_to_angle(a_abs: float, b_abs: float, angle: float) -> float:
    sep = abs(a_abs - b_abs) % 360
    if sep > 180:
        sep = 360 - sep
    return abs(sep - angle)


def _natal_targets(natal_cd: dict, birth_time_known: bool) -> dict:
    targets = {p["body"]: _abs(p["sign"], p["degree"]) for p in natal_cd["planets"]}
    for p in natal_cd["points"]:
        if p["body"] in ("Chiron", "North Node"):
            targets[p["body"]] = _abs(p["sign"], p["degree"])
    if birth_time_known:
        targets["ASC"] = _abs(natal_cd["angles"]["ASC"]["sign"], natal_cd["angles"]["ASC"]["degree"])
        targets["MC"] = _abs(natal_cd["angles"]["MC"]["sign"], natal_cd["angles"]["MC"]["degree"])
    return targets


def find_transits(natal_birth: dict, on_date: str, birth_time_known: bool) -> list:
    natal_cd = build_chart_data(natal_birth)
    targets = _natal_targets(natal_cd, birth_time_known)
    lat, lon, tz = natal_birth["lat"], natal_birth["lon"], natal_birth["tz"]
    hs = natal_birth.get("house_system") or "Placidus"

    pos_today = _positions(on_date, lat, lon, tz, hs)
    y, mo, d = (int(x) for x in on_date.split("-"))
    next_date = (date(y, mo, d) + timedelta(days=1)).isoformat()
    pos_tomorrow = _positions(next_date, lat, lon, tz, hs)

    transits = []
    for mover in MOVERS:
        is_moon = mover == "Moon"
        for tname, tpos in targets.items():
            res = _aspect_between(pos_today[mover], tpos, is_moon)
            if res is None:
                continue
            atype, orb = res
            angle = ANGLE_OF[atype]
            orb_tomorrow = _orb_to_angle(pos_tomorrow[mover], tpos, angle)
            motion = "applying" if orb_tomorrow < orb else "separating"
            transits.append({"mover": mover, "type": atype, "target": tname,
                             "orb": orb, "motion": motion})
    return transits


def _fmt(t: dict) -> str:
    line = (f"- transiting {t['mover']} {t['type']} natal {t['target']} "
            f"(orb {t['orb']}°, {t['motion']})")
    if t["mover"] == "Moon":
        line += " — Moon approximate (noon)"
    return line


def render_markdown(transits: list, meta: dict) -> str:
    lines = [f"# Transits for {meta['name']} — {meta['on']}", "",
             f"Natal: {meta['natal_date']}, {meta['city']}. "
             f"Transiting positions at noon on {meta['on']}.", ""]

    slow = sorted((t for t in transits if t["mover"] in SLOW_MOVERS), key=lambda t: t["orb"])
    fast = sorted((t for t in transits if t["mover"] not in SLOW_MOVERS), key=lambda t: t["orb"])

    lines.append("## Slow / outer transits (longer-lasting, most significant)")
    lines += [_fmt(t) for t in slow] if slow else ["- (none in orb)"]
    lines += ["", "## Fast / inner transits (days to weeks)"]
    lines += [_fmt(t) for t in fast] if fast else ["- (none in orb)"]

    lines += ["", "## Notes",
              "Transiting Moon is at noon on the snapshot date — its exact degree is approximate."]
    if not meta["birth_time_known"]:
        lines.append("Natal birth time unknown → transits to the natal Ascendant/MC are omitted, "
                     "and natal-Moon aspects are approximate.")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Transit snapshot (natal vs. a date) via kerykeion.")
    ap.add_argument("--name", default="Chart")
    ap.add_argument("--date", required=True, help="natal birth date YYYY-MM-DD")
    ap.add_argument("--time", default=None, help="natal birth time HH:MM (optional; omit if unknown)")
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--tz", required=True)
    ap.add_argument("--city", default="")
    ap.add_argument("--house-system", default="Placidus")
    ap.add_argument("--on", default=None, help="snapshot date YYYY-MM-DD (default: today)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    try:
        y, mo, d = (int(x) for x in args.date.split("-"))
        birth_time_known = args.time is not None
        hh, mm = ((int(x) for x in args.time.split(":")) if birth_time_known else (12, 0))
        natal = {"name": args.name, "year": y, "month": mo, "day": d, "hour": hh, "minute": mm,
                 "lat": args.lat, "lon": args.lon, "tz": args.tz, "city": args.city,
                 "house_system": args.house_system}
        on_date = args.on or date.today().isoformat()
        int(on_date.split("-")[0]); int(on_date.split("-")[1]); int(on_date.split("-")[2])
        transits = find_transits(natal, on_date, birth_time_known)
        meta = {"name": args.name, "on": on_date, "natal_date": args.date,
                "city": args.city, "birth_time_known": birth_time_known}
    except Exception as e:  # noqa: BLE001 — clean message, no traceback
        print(f"Error: {e}", file=sys.stderr)
        return 1

    report = render_markdown(transits, meta)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Wrote {args.out}. Keep it private.")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
