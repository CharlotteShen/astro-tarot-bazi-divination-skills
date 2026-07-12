"""Route A transit forecast timeline: over a date range, find each transit-to-natal aspect and its
exact perfection date(s) — including retrograde multi-passes — with a ±1° in-effect window. Reuses
transits.py + chart.py. One daily scan is cached; a pure _scan_series finds zero-crossings.
"""
import argparse
import sys
from datetime import date, timedelta

from chart import build_chart_data
from transits import _positions, _natal_targets, SLOW_MOVERS

# --- v1.2.1 forecast tuning (own conventions — adjust freely) ---
FORECAST_MOVERS = ["Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Chiron", "North Node", "Mars"]
EXACT_OFFSETS = {"conjunction": [0], "opposition": [180], "trine": [120, -120],
                 "square": [90, -90], "sextile": [60, -60]}
WINDOW_ORB = 1.0   # ° — a transit is "in effect" within this orb of exact


def _wrap180(x):
    return ((x + 180) % 360) - 180


def _positions_over_range(from_date, to_date, lat, lon, tz, house_system="Placidus"):
    y0, m0, d0 = (int(x) for x in from_date.split("-"))
    y1, m1, d1 = (int(x) for x in to_date.split("-"))
    cur, end = date(y0, m0, d0), date(y1, m1, d1)
    series = []
    while cur <= end:
        series.append((cur, _positions(cur.isoformat(), lat, lon, tz, house_system)))
        cur += timedelta(days=1)
    return series


def _scan_series(dates, signed, retro):
    out = []
    n = len(signed)
    for i in range(n - 1):
        a, b = signed[i], signed[i + 1]
        # A real crossing steps through 0 with a tiny gap; the _wrap180 discontinuity at ±180
        # (the aspect's anti-point) jumps ~+179 -> ~-179, a false sign change — exclude it via |a-b|<180.
        if a == 0 or (a * b < 0 and abs(a - b) < 180):
            denom = abs(a) + abs(b)
            frac = abs(a) / denom if denom > 0 else 0.0
            cross = dates[i] + timedelta(days=round(frac))
            lo = i
            while lo > 0 and abs(signed[lo - 1]) <= WINDOW_ORB:
                lo -= 1
            hi = i + 1
            while hi < n - 1 and abs(signed[hi + 1]) <= WINDOW_ORB:
                hi += 1
            out.append({"date": cross, "rx": retro[i], "window": (dates[lo], dates[hi])})
    return out


def find_forecast(natal_birth, from_date, to_date, birth_time_known):
    natal_cd = build_chart_data(natal_birth)
    targets = _natal_targets(natal_cd, birth_time_known)
    lat, lon, tz = natal_birth["lat"], natal_birth["lon"], natal_birth["tz"]
    hs = natal_birth.get("house_system") or "Placidus"

    series = _positions_over_range(from_date, to_date, lat, lon, tz, hs)
    dates = [d for d, _ in series]
    lonmap = {m: [pos[m] for _, pos in series] for m in FORECAST_MOVERS}
    retromap = {m: [_wrap180(lonmap[m][i + 1] - lonmap[m][i]) < 0 for i in range(len(dates) - 1)] + [False]
                for m in FORECAST_MOVERS}

    grouped = {}
    for m in FORECAST_MOVERS:
        mlon, mretro = lonmap[m], retromap[m]
        for tname, tpos in targets.items():
            for atype, offsets in EXACT_OFFSETS.items():
                for o in offsets:
                    signed = [_wrap180(mlon[i] - (tpos + o)) for i in range(len(dates))]
                    for perf in _scan_series(dates, signed, mretro):
                        grouped.setdefault((m, tname, atype), []).append(perf)

    entries = []
    for (m, tname, atype), perfs in grouped.items():
        perfs.sort(key=lambda p: p["date"])
        entries.append({
            "mover": m, "target": tname, "aspect": atype,
            "exact_dates": [{"date": p["date"], "rx": p["rx"]} for p in perfs],
            "window": (min(p["window"][0] for p in perfs), max(p["window"][1] for p in perfs)),
        })
    entries.sort(key=lambda e: e["exact_dates"][0]["date"])
    return {
        "entries": entries,
        "meta": {"name": natal_birth.get("name", ""), "city": natal_birth.get("city", ""),
                 "natal_date": f"{natal_birth['year']:04d}-{natal_birth['month']:02d}-{natal_birth['day']:02d}",
                 "from": from_date, "to": to_date, "birth_time_known": birth_time_known},
    }


def _fmt_entry(e):
    exacts = ", ".join(f"{d['date'].isoformat()}{' (Rx)' if d['rx'] else ''}" for d in e["exact_dates"])
    enter, exit_ = e["window"]
    first = e["exact_dates"][0]["date"].isoformat()
    return (f"- {first} — transiting {e['mover']} {e['aspect']} natal {e['target']} — "
            f"exact {exacts}; in effect {enter.isoformat()} → {exit_.isoformat()}")


def render_markdown(result):
    m = result["meta"]
    lines = [f"# Transit forecast for {m['name']} — {m['from']} to {m['to']}", "",
             f"Natal: {m['natal_date']}, {m['city']}. Forecast movers: {', '.join(FORECAST_MOVERS)}.", ""]

    major = [e for e in result["entries"] if e["mover"] in SLOW_MOVERS]
    mars = [e for e in result["entries"] if e["mover"] not in SLOW_MOVERS]

    lines.append("## Major transits (Jupiter and slower — longer-lasting)")
    lines += [_fmt_entry(e) for e in major] if major else ["- (none in this range)"]
    lines += ["", "## Mars triggers (fast, days-long)"]
    lines += [_fmt_entry(e) for e in mars] if mars else ["- (none in this range)"]

    if not m["birth_time_known"]:
        lines += ["", "## Notes",
                  "Natal birth time unknown → transits to the natal Ascendant/MC are omitted."]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Transit forecast timeline (natal vs. a date range) via kerykeion.")
    ap.add_argument("--name", default="Chart")
    ap.add_argument("--date", required=True, help="natal birth date YYYY-MM-DD")
    ap.add_argument("--time", default=None, help="natal birth time HH:MM (optional; omit if unknown)")
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--tz", required=True)
    ap.add_argument("--city", default="")
    ap.add_argument("--house-system", default="Placidus")
    ap.add_argument("--from", dest="from_date", default=None, help="range start YYYY-MM-DD (default today)")
    ap.add_argument("--to", dest="to_date", default=None, help="range end YYYY-MM-DD (default from+365d)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    try:
        y, mo, d = (int(x) for x in args.date.split("-"))
        birth_time_known = args.time is not None
        hh, mm = ((int(x) for x in args.time.split(":")) if birth_time_known else (12, 0))
        natal = {"name": args.name, "year": y, "month": mo, "day": d, "hour": hh, "minute": mm,
                 "lat": args.lat, "lon": args.lon, "tz": args.tz, "city": args.city,
                 "house_system": args.house_system}
        from_date = args.from_date or date.today().isoformat()
        fy, fm, fd = (int(x) for x in from_date.split("-"))
        to_date = args.to_date or (date(fy, fm, fd) + timedelta(days=365)).isoformat()
        ty, tm, td = (int(x) for x in to_date.split("-"))
        if date(ty, tm, td) < date(fy, fm, fd):
            raise ValueError(f"--to {to_date} is before --from {from_date}")
        result = find_forecast(natal, from_date, to_date, birth_time_known)
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
