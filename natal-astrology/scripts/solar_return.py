"""Route A Solar Return: cast and read the chart for the moment the Sun returns to its natal
longitude each year, plus a bridge onto the natal chart. Default at the birth location; optional
relocated. Reuses chart.py + sensitivity.py. No new ephemeris API.
"""
import argparse
import sys
from datetime import datetime, timedelta

import pytz

from chart import (build_chart_data, _subject, ASPECT_DEFS, _ang_dist, find_house,
                   _abs_pos, CUSP_ATTRS)
from sensitivity import _abs

SR_TO_NATAL_ORB = 2.0   # ° — tight orb for SR key points to natal planets/angles
SR_TARGETS = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
              "Uranus", "Neptune", "Pluto", "ASC", "MC"]
SR_POINTS = ["SR ASC", "SR MC", "SR Sun", "SR Moon"]


def _wrap180(x):
    return ((x + 180) % 360) - 180


def _pabs(cd, body):
    p = next(x for x in cd["planets"] if x["body"] == body)
    return _abs(p["sign"], p["degree"])


def _sun_longitude(dt_utc: datetime) -> float:
    cd = build_chart_data({"name": "s", "year": dt_utc.year, "month": dt_utc.month,
                           "day": dt_utc.day, "hour": dt_utc.hour, "minute": dt_utc.minute,
                           "lat": 0.0, "lon": 0.0, "tz": "UTC", "city": "",
                           "house_system": "Placidus"})
    return _pabs(cd, "Sun")


def find_sr_moment(natal_sun_lon: float, year: int, month: int, day: int) -> datetime:
    base = datetime(year, month, day) - timedelta(days=2)
    prev = None
    lo = hi = None
    for k in range(0, 24 * 5):
        t = base + timedelta(hours=k)
        s = _wrap180(_sun_longitude(t) - natal_sun_lon)
        if prev is not None and prev[1] * s <= 0:   # <= handles a sample landing exactly on the return
            lo, hi = prev[0], t
            break
        prev = (t, s)
    if lo is None:
        raise ValueError("no solar return found in the search window")
    while (hi - lo) > timedelta(minutes=1):
        mid = lo + (hi - lo) / 2
        if _wrap180(_sun_longitude(lo) - natal_sun_lon) * _wrap180(_sun_longitude(mid) - natal_sun_lon) <= 0:
            hi = mid
        else:
            lo = mid
    return hi.replace(second=0, microsecond=0)


def _bridge(sr_chart: dict, natal_cd: dict, natal_cusps: list) -> dict:
    natal_abs = {p["body"]: _abs(p["sign"], p["degree"]) for p in natal_cd["planets"]}
    natal_abs["ASC"] = _abs(natal_cd["angles"]["ASC"]["sign"], natal_cd["angles"]["ASC"]["degree"])
    natal_abs["MC"] = _abs(natal_cd["angles"]["MC"]["sign"], natal_cd["angles"]["MC"]["degree"])

    sr_pts = {
        "SR ASC": _abs(sr_chart["angles"]["ASC"]["sign"], sr_chart["angles"]["ASC"]["degree"]),
        "SR MC": _abs(sr_chart["angles"]["MC"]["sign"], sr_chart["angles"]["MC"]["degree"]),
        "SR Sun": _pabs(sr_chart, "Sun"),
        "SR Moon": _pabs(sr_chart, "Moon"),
    }
    overlay = {name: find_house(lon, natal_cusps) for name, lon in sr_pts.items()}

    contacts = []
    for aname, alon in sr_pts.items():
        for tname in SR_TARGETS:
            sep = _ang_dist(alon, natal_abs[tname])
            for atype, angle, _orb in ASPECT_DEFS:
                if abs(sep - angle) <= SR_TO_NATAL_ORB:
                    contacts.append({"a": aname, "type": atype, "b": tname,
                                     "orb": round(abs(sep - angle), 2)})
                    break
    return {"overlay": overlay, "contacts": contacts}


def build_solar_return(natal_birth: dict, year: int, sr_location: dict = None) -> dict:
    natal_cd = build_chart_data(natal_birth)
    natal_sun = _pabs(natal_cd, "Sun")
    natal_cusps = [_abs_pos(getattr(_subject(natal_birth), a)) for a in CUSP_ATTRS]
    birth_time_known = natal_birth.get("time_known", True)

    sr_utc = find_sr_moment(natal_sun, year, natal_birth["month"], natal_birth["day"])
    loc = sr_location or {"lat": natal_birth["lat"], "lon": natal_birth["lon"],
                          "tz": natal_birth["tz"], "city": natal_birth.get("city", "")}
    sr_chart = build_chart_data({
        "name": "SR", "year": sr_utc.year, "month": sr_utc.month, "day": sr_utc.day,
        "hour": sr_utc.hour, "minute": sr_utc.minute, "lat": loc["lat"], "lon": loc["lon"],
        "tz": "UTC", "city": loc.get("city", ""),
        "house_system": natal_birth.get("house_system", "Placidus")})
    sr_local = pytz.utc.localize(sr_utc).astimezone(pytz.timezone(loc["tz"]))

    return {
        "sr_utc": sr_utc, "sr_local": sr_local,
        "location": {"city": loc.get("city", ""), "relocated": sr_location is not None},
        "sr_chart": sr_chart,
        "bridge": _bridge(sr_chart, natal_cd, natal_cusps),
        "meta": {"name": natal_birth.get("name", ""), "year": year,
                 "natal_date": f"{natal_birth['year']:04d}-{natal_birth['month']:02d}-{natal_birth['day']:02d}",
                 "birth_time_known": birth_time_known},
    }


def render_markdown(result: dict) -> str:
    m, loc = result["meta"], result["location"]
    sr = result["sr_chart"]
    asc, mc = sr["angles"]["ASC"], sr["angles"]["MC"]
    by = {p["body"]: p for p in sr["planets"]}
    sun, moon = by["Sun"], by["Moon"]
    where = "relocated" if loc["relocated"] else "birth location"

    lines = [f"# Solar Return {m['year']} — {m['name']}", "",
             f"Return: {result['sr_utc']:%Y-%m-%d %H:%M} UT "
             f"({result['sr_local']:%Y-%m-%d %H:%M} local) · cast for {loc['city']} ({where})", "",
             "## The year's chart (Solar Return)",
             f"- SR Ascendant: {asc['sign']} {asc['degree']}°   ·   SR MC: {mc['sign']} {mc['degree']}°",
             f"- SR Sun: {sun['sign']} {sun['degree']}° (SR house {sun['house']})   ·   "
             f"SR Moon: {moon['sign']} {moon['degree']}° (SR house {moon['house']})"]

    on_angles = []
    for a in sr["aspects"]:
        if a["type"] != "conjunction":
            continue
        pair = {a["a"], a["b"]}
        if "ASC" in pair or "MC" in pair:
            angle = "ASC" if "ASC" in pair else "MC"
            planet = (pair - {angle}).pop()
            if planet not in ("ASC", "MC"):
                on_angles.append(f"{planet} on {angle}")
    lines.append("- Planets on the SR angles: " + (", ".join(on_angles) if on_angles else "(none tight)"))

    lines += ["", "## Bridge to your natal chart"]
    ov, cts = result["bridge"]["overlay"], result["bridge"]["contacts"]
    for pt in SR_POINTS:
        pt_contacts = [f"{c['type']} natal {c['b']} ({c['orb']}°)" for c in cts if c["a"] == pt]
        tail = ("; " + ", ".join(pt_contacts)) if pt_contacts else ""
        lines.append(f"- {pt} → your natal house {ov[pt]}{tail}")

    lines += ["", "## Notes"]
    if not m["birth_time_known"]:
        lines.append("Natal birth time unknown → the SR angles, houses, and this bridge are unreliable "
                     "(the return moment shifts with the natal Sun); only the SR planet signs (not the "
                     "fast Moon) are usable.")
    else:
        lines.append("SR angles and houses are computed for the return instant at the chosen location.")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Solar Return chart + natal bridge via kerykeion.")
    ap.add_argument("--name", default="Chart")
    ap.add_argument("--date", required=True, help="natal birth date YYYY-MM-DD")
    ap.add_argument("--time", default=None, help="natal birth time HH:MM (optional; omit if unknown)")
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--tz", required=True)
    ap.add_argument("--city", default="")
    ap.add_argument("--house-system", default="Placidus")
    ap.add_argument("--year", type=int, default=None, help="solar-return year (default: current year)")
    ap.add_argument("--loc-lat", type=float, default=None)
    ap.add_argument("--loc-lon", type=float, default=None)
    ap.add_argument("--loc-tz", default=None)
    ap.add_argument("--loc-city", default="")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    try:
        y, mo, d = (int(x) for x in args.date.split("-"))
        birth_time_known = args.time is not None
        hh, mm = ((int(x) for x in args.time.split(":")) if birth_time_known else (12, 0))
        natal = {"name": args.name, "year": y, "month": mo, "day": d, "hour": hh, "minute": mm,
                 "lat": args.lat, "lon": args.lon, "tz": args.tz, "city": args.city,
                 "house_system": args.house_system, "time_known": birth_time_known}
        loc = None
        if any(v is not None for v in (args.loc_lat, args.loc_lon, args.loc_tz)):
            if args.loc_lat is None or args.loc_lon is None or args.loc_tz is None:
                raise ValueError("relocated SR needs --loc-lat, --loc-lon and --loc-tz together")
            loc = {"lat": args.loc_lat, "lon": args.loc_lon, "tz": args.loc_tz, "city": args.loc_city}
        from datetime import date as _date
        year = args.year if args.year is not None else _date.today().year
        result = build_solar_return(natal, year, sr_location=loc)
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
