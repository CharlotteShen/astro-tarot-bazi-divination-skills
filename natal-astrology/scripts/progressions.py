"""Route A secondary progressions: the progressed personal points (day-for-a-year, full-recompute —
same sourced convention as rectification.py), the progressed lunation phase, and tight (<=1 degree)
progressed-to-natal contacts. Reuses chart.py + sensitivity.py.
"""
import argparse
import sys
from datetime import date, datetime, timedelta

from chart import (build_chart_data, _subject, _abs_pos, CUSP_ATTRS, ASPECT_DEFS,
                   _ang_dist, find_house, SIGNS)
from sensitivity import _abs

PROG_BODIES = ["Sun", "Moon", "Mercury", "Venus", "Mars"]
POINT_ORDER = ["prog Sun", "prog Moon", "prog Mercury", "prog Venus", "prog Mars",
               "prog ASC", "prog MC"]
PROG_ORB = 1.0     # deg — standard progression tightness (prog Moon ~1deg/month, prog Sun ~1deg/year)
YEAR_DAYS = 365.25
PHASES = ["New", "Crescent", "First Quarter", "Gibbous", "Full", "Disseminating",
          "Last Quarter", "Balsamic"]
PHASE_MEANING = {
    "New": "seeding — a new ~30-year cycle begins in the dark",
    "Crescent": "first efforts against resistance; committing to the seed",
    "First Quarter": "decisive building; a crisis of action",
    "Gibbous": "refining and adjusting toward the goal",
    "Full": "culmination and visibility; the cycle's meaning revealed",
    "Disseminating": "sharing and teaching what the cycle built; harvest turns outward",
    "Last Quarter": "reorienting; questioning structures, composting what's done",
    "Balsamic": "release and endings; clearing space before the next seed",
}


def _phase(elongation: float) -> str:
    return PHASES[int((elongation % 360) // 45)]


def _progressed_datetime(natal_birth: dict, ref_date: date):
    birth_dt = datetime(natal_birth["year"], natal_birth["month"], natal_birth["day"],
                        natal_birth["hour"], natal_birth["minute"])
    ref_dt = datetime(ref_date.year, ref_date.month, ref_date.day, 12, 0)
    age_years = (ref_dt - birth_dt).total_seconds() / (YEAR_DAYS * 86400)
    return birth_dt + timedelta(days=age_years), age_years


def build_progressions(natal_birth: dict, ref_date: date) -> dict:
    prog_dt, age = _progressed_datetime(natal_birth, ref_date)
    prog_cd = build_chart_data(dict(natal_birth, year=prog_dt.year, month=prog_dt.month,
                                    day=prog_dt.day, hour=prog_dt.hour, minute=prog_dt.minute))
    natal_cd = build_chart_data(natal_birth)
    natal_cusps = [_abs_pos(getattr(_subject(natal_birth), a)) for a in CUSP_ATTRS]
    natal_abs = {p["body"]: _abs(p["sign"], p["degree"]) for p in natal_cd["planets"]}
    natal_abs["ASC"] = _abs(natal_cd["angles"]["ASC"]["sign"], natal_cd["angles"]["ASC"]["degree"])
    natal_abs["MC"] = _abs(natal_cd["angles"]["MC"]["sign"], natal_cd["angles"]["MC"]["degree"])

    lons = {}
    for b in PROG_BODIES:
        p = next(x for x in prog_cd["planets"] if x["body"] == b)
        lons[f"prog {b}"] = _abs(p["sign"], p["degree"])
    lons["prog ASC"] = _abs(prog_cd["angles"]["ASC"]["sign"], prog_cd["angles"]["ASC"]["degree"])
    lons["prog MC"] = _abs(prog_cd["angles"]["MC"]["sign"], prog_cd["angles"]["MC"]["degree"])

    points = {name: {"sign": SIGNS[int(lon // 30)], "degree": round(lon % 30, 2),
                     "natal_house": find_house(lon, natal_cusps)}
              for name, lon in lons.items()}

    elong = (lons["prog Moon"] - lons["prog Sun"]) % 360
    lunation = {"elongation": round(elong, 1), "phase": _phase(elong)}

    hits = []
    for name, lon in lons.items():
        for tname, tlon in natal_abs.items():
            sep = _ang_dist(lon, tlon)
            for atype, angle, _orb in ASPECT_DEFS:
                if abs(sep - angle) <= PROG_ORB:
                    hits.append({"a": name, "type": atype, "b": tname,
                                 "orb": round(abs(sep - angle), 2)})
                    break
    hits.sort(key=lambda h: h["orb"])

    return {"points": points, "lunation": lunation, "hits": hits,
            "meta": {"name": natal_birth.get("name", ""), "age": round(age, 2),
                     "prog_datetime": prog_dt.strftime("%Y-%m-%d %H:%M"),
                     "ref_date": ref_date.isoformat(),
                     "birth_time_known": natal_birth.get("time_known", True)}}


def render_markdown(result: dict) -> str:
    m, lun = result["meta"], result["lunation"]
    lines = [f"# Secondary Progressions — {m['name']} (as of {m['ref_date']})", "",
             f"Age {m['age']} · progressed chart for {m['prog_datetime']} (day-for-a-year)", "",
             "## Progressed points"]
    for name in POINT_ORDER:
        p = result["points"][name]
        lines.append(f"- {name}: {p['sign']} {p['degree']}° → your natal house {p['natal_house']}")

    lines += ["", "## Progressed lunation phase",
              f"{lun['phase']} ({lun['elongation']}°) — {PHASE_MEANING[lun['phase']]}",
              "", "## Progressed-to-natal contacts (≤1°)"]
    lines += ([f"- {h['a']} {h['type']} natal {h['b']} ({h['orb']}°)" for h in result["hits"]]
              if result["hits"] else ["- (none in orb)"])

    lines += ["", "## Notes"]
    if m["birth_time_known"]:
        lines.append("Progressed angles and house placements are computed from your birth time and place.")
    else:
        lines.append("Birth time unknown → progressed ASC/MC, all natal-house placements, the prog "
                     "Moon's exact degree, and the lunation phase are unreliable; prog Sun/Mercury/"
                     "Venus/Mars signs remain usable.")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Secondary progressions via kerykeion.")
    ap.add_argument("--name", default="Chart")
    ap.add_argument("--date", required=True, help="natal birth date YYYY-MM-DD")
    ap.add_argument("--time", default=None, help="natal birth time HH:MM (optional; omit if unknown)")
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--tz", required=True)
    ap.add_argument("--city", default="")
    ap.add_argument("--house-system", default="Placidus")
    ap.add_argument("--on", default=None, help="reference date YYYY-MM-DD (default: today)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    try:
        y, mo, d = (int(x) for x in args.date.split("-"))
        birth_time_known = args.time is not None
        hh, mm = ((int(x) for x in args.time.split(":")) if birth_time_known else (12, 0))
        natal = {"name": args.name, "year": y, "month": mo, "day": d, "hour": hh, "minute": mm,
                 "lat": args.lat, "lon": args.lon, "tz": args.tz, "city": args.city,
                 "house_system": args.house_system, "time_known": birth_time_known}
        if args.on:
            ry, rmo, rd = (int(x) for x in args.on.split("-"))
            ref = date(ry, rmo, rd)
        else:
            ref = date.today()
        result = build_progressions(natal, ref)
    except Exception as e:  # noqa: BLE001 — clean message, no traceback
        print(f"Error: {e}", file=sys.stderr)
        return 1

    report = render_markdown(result)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Wrote {args.out}. Keep it private.")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
