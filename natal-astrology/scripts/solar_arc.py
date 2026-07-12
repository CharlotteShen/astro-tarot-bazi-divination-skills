"""Route A solar arc directions: every natal point advanced by the exact progressed-Sun arc
(day-for-a-year via progressions._progressed_datetime), checked against the natal chart at a tight
1-degree orb, with per-contact timing (orb converts to time at the actual arc rate, ~1 deg/year).
"""
import argparse
import sys
from datetime import date, timedelta

from chart import build_chart_data, ASPECT_DEFS, _ang_dist
from sensitivity import _abs
from progressions import _progressed_datetime

SA_ORB = 1.0   # ° — standard directions tightness; orb ≈ years from exact


def _self_aspect(arc: float):
    d = arc % 360
    if d > 180:
        d = 360 - d
    for atype, angle, _orb in ASPECT_DEFS:
        if abs(d - angle) <= SA_ORB:
            return {"type": atype, "orb": round(abs(d - angle), 2)}
    return None


def _arc(natal_birth: dict, ref_date: date) -> float:
    prog_dt, _age = _progressed_datetime(natal_birth, ref_date)
    prog_cd = build_chart_data(dict(natal_birth, year=prog_dt.year, month=prog_dt.month,
                                    day=prog_dt.day, hour=prog_dt.hour, minute=prog_dt.minute))
    natal_cd = build_chart_data(natal_birth)
    ps = next(p for p in prog_cd["planets"] if p["body"] == "Sun")
    ns = next(p for p in natal_cd["planets"] if p["body"] == "Sun")
    return (_abs(ps["sign"], ps["degree"]) - _abs(ns["sign"], ns["degree"])) % 360


def build_solar_arc(natal_birth: dict, ref_date: date) -> dict:
    arc = _arc(natal_birth, ref_date)
    rate = _arc(natal_birth, ref_date + timedelta(days=365)) - arc

    natal_cd = build_chart_data(natal_birth)
    natal_abs = {p["body"]: _abs(p["sign"], p["degree"]) for p in natal_cd["planets"]}
    natal_abs["ASC"] = _abs(natal_cd["angles"]["ASC"]["sign"], natal_cd["angles"]["ASC"]["degree"])
    natal_abs["MC"] = _abs(natal_cd["angles"]["MC"]["sign"], natal_cd["angles"]["MC"]["degree"])

    step = rate * 30 / 365.25   # 30-day probe for applying/separating
    hits = []
    for dname, nlon in natal_abs.items():
        d_now = (nlon + arc) % 360
        d_30 = (nlon + arc + step) % 360
        for tname, tlon in natal_abs.items():
            if tname == dname:
                continue
            sep = _ang_dist(d_now, tlon)
            for atype, angle, _orb in ASPECT_DEFS:
                if abs(sep - angle) <= SA_ORB:
                    orb = abs(sep - angle)
                    orb30 = abs(_ang_dist(d_30, tlon) - angle)
                    motion = "applying" if orb30 < orb else "separating"
                    hits.append({"a": f"SA {dname}", "type": atype, "b": tname,
                                 "orb": round(orb, 2), "motion": motion,
                                 "months": int(round(orb / rate * 12))})
                    break
    hits.sort(key=lambda h: h["orb"])

    return {"hits": hits, "self_aspect": _self_aspect(arc),
            "meta": {"name": natal_birth.get("name", ""), "ref_date": ref_date.isoformat(),
                     "arc": round(arc, 2), "rate": round(rate, 3),
                     "birth_time_known": natal_birth.get("time_known", True)}}


def render_markdown(result: dict) -> str:
    m = result["meta"]
    lines = [f"# Solar Arc Directions — {m['name']} (as of {m['ref_date']})", "",
             f"Arc {m['arc']}° · rate {m['rate']}°/yr (exact progressed-Sun arc, day-for-a-year)", "",
             "## Directed contacts (≤1°)"]
    if result["hits"]:
        for h in result["hits"]:
            timing = (f"exact in ~{h['months']} months" if h["motion"] == "applying"
                      else f"exact ~{h['months']} months ago")
            lines.append(f"- {h['a']} {h['type']} natal {h['b']} ({h['orb']}°, {h['motion']} — {timing})")
    else:
        lines.append("- (none in orb)")

    if result["self_aspect"]:
        sa = result["self_aspect"]
        lines += ["", "## Whole-chart note",
                  f"The arc is within {sa['orb']}° of a {sa['type']} — the entire directed chart "
                  "aspects its own natal positions this year."]

    lines += ["", "## Notes"]
    if m["birth_time_known"]:
        lines.append("Directed angles computed from your birth time; timing estimates are approximate "
                     "to about a month.")
    else:
        lines.append("Birth time unknown → directed ASC/MC and contacts to the natal ASC/MC are "
                     "unreliable, and arc timing carries ~±6 months extra uncertainty; "
                     "planet-to-planet contacts remain usable.")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Solar arc directions via kerykeion.")
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
        result = build_solar_arc(natal, ref)
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
