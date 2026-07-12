"""Route A lightweight rectification: score candidate birth times in a range against dated life
events, using two classical techniques — progressed angles/Moon and transits to the natal angles.
Heuristic corroboration only; never a declared 'true' time. Reuses chart.py + sensitivity.py.
"""
import argparse
import sys
from datetime import datetime, timedelta

from chart import ASPECT_DEFS, build_chart_data
from sensitivity import (_range_offsets, _birth_at_offset, _abs,
                         COARSE_STEP_MINUTES, PLANET_NAMES)

TOP_N_DISPLAYED = 8            # how many ranked candidates the report shows (own choice, tunable)
YEAR_DAYS = 365.25             # secondary-progression "day-for-a-year" mean year


def _progressed_birth(birth: dict, event_date: str) -> dict:
    birth_dt = datetime(birth["year"], birth["month"], birth["day"],
                        birth["hour"], birth["minute"])
    ey, em, ed = (int(x) for x in event_date.split("-"))
    event_dt = datetime(ey, em, ed, 12, 0)   # noon reference; time-of-day negligible at year scale
    age_years = (event_dt - birth_dt).total_seconds() / (YEAR_DAYS * 86400)
    prog_dt = birth_dt + timedelta(days=age_years)
    return dict(birth, year=prog_dt.year, month=prog_dt.month, day=prog_dt.day,
                hour=prog_dt.hour, minute=prog_dt.minute)


def _transit_positions(event_date: str, lat, lon, tz, house_system="Placidus") -> dict:
    ey, em, ed = (int(x) for x in event_date.split("-"))
    tb = {"name": "transit", "year": ey, "month": em, "day": ed, "hour": 12, "minute": 0,
          "lat": lat, "lon": lon, "tz": tz, "city": "", "house_system": house_system}
    cd = build_chart_data(tb)
    return {p["body"]: _abs(p["sign"], p["degree"]) for p in cd["planets"]}


def _hits(movers: dict, targets: dict, kind: str) -> list:
    hits = []
    for mname, mpos in movers.items():
        for tname, tpos in targets.items():
            sep = abs(mpos - tpos) % 360
            if sep > 180:
                sep = 360 - sep
            for atype, angle, orb in ASPECT_DEFS:
                if abs(sep - angle) <= orb:
                    hits.append({"kind": kind, "moving": mname, "target": tname,
                                 "type": atype, "orb": round(abs(sep - angle), 2)})
                    break
    return hits


def _natal_targets(cd: dict) -> dict:
    targets = {p["body"]: _abs(p["sign"], p["degree"]) for p in cd["planets"]}
    targets["ASC"] = _abs(cd["angles"]["ASC"]["sign"], cd["angles"]["ASC"]["degree"])
    targets["MC"] = _abs(cd["angles"]["MC"]["sign"], cd["angles"]["MC"]["degree"])
    return targets


def score_candidate(birth: dict, events: list, transit_cache: list) -> dict:
    cd = build_chart_data(birth)
    natal = _natal_targets(cd)
    natal_angles = {"ASC": natal["ASC"], "MC": natal["MC"]}

    score = 0
    event_results = []
    for i, ev in enumerate(events):
        pcd = build_chart_data(_progressed_birth(birth, ev["date"]))
        pmoon = next(p for p in pcd["planets"] if p["body"] == "Moon")
        prog_movers = {
            "ASC": _abs(pcd["angles"]["ASC"]["sign"], pcd["angles"]["ASC"]["degree"]),
            "MC": _abs(pcd["angles"]["MC"]["sign"], pcd["angles"]["MC"]["degree"]),
            "Moon": _abs(pmoon["sign"], pmoon["degree"]),
        }
        hits = _hits(prog_movers, natal, "progressed") + \
            _hits(transit_cache[i], natal_angles, "transit")
        score += len(hits)
        event_results.append({"date": ev["date"], "label": ev["label"], "hits": hits})
    return {"score": score, "events": event_results}


def analyze(birth: dict, start: str, end: str, events: list) -> dict:
    lat, lon, tz = birth["lat"], birth["lon"], birth["tz"]
    hs = birth.get("house_system") or "Placidus"
    transit_cache = [_transit_positions(ev["date"], lat, lon, tz, hs) for ev in events]

    base_dt, offsets = _range_offsets(birth, start, end, COARSE_STEP_MINUTES)
    ranked = []
    for off in offsets:
        cand = _birth_at_offset(birth, base_dt, off)
        sc = score_candidate(cand, events, transit_cache)
        ranked.append({"time": (base_dt + timedelta(minutes=off)).strftime("%H:%M"),
                       "score": sc["score"], "events": sc["events"]})
    ranked.sort(key=lambda r: r["score"], reverse=True)
    return {
        "ranked": ranked,
        "meta": {"name": birth.get("name", ""),
                 "date": f"{birth['year']:04d}-{birth['month']:02d}-{birth['day']:02d}",
                 "start": start, "end": end, "city": birth.get("city", ""),
                 "candidate_count": len(offsets)},
    }


def render_markdown(result: dict, birth: dict, start: str, end: str, events: list) -> str:
    m = result["meta"]
    lines = [f"# Rectification report — {m['name']}", "",
             f"Range checked: {m['date']}, {start}–{end} "
             f"({m['candidate_count']} candidates, {COARSE_STEP_MINUTES}-minute step)",
             "Events considered:"]
    for i, ev in enumerate(events, 1):
        lines.append(f'  {i}. "{ev["label"]}" — {ev["date"]}')

    lines += ["", f"## Ranked candidate times (best corroboration first, "
                  f"top {TOP_N_DISPLAYED} of {m['candidate_count']} checked)"]
    for rank, cand in enumerate(result["ranked"][:TOP_N_DISPLAYED], 1):
        lines.append(f"{rank}. {cand['time']} — score {cand['score']}")
        for ev in cand["events"]:
            if not ev["hits"]:
                continue
            parts = [f"{h['kind']} {h['moving']} {h['type']} natal {h['target']} (orb {h['orb']}°)"
                     for h in ev["hits"]]
            lines.append(f'   - "{ev["label"]}" ({ev["date"]}): ' + "; ".join(parts))

    lines += ["", "## Caveat",
              "This is a heuristic aid based on two classical rectification techniques (progressed "
              "angles/Moon + transits to the angles), not proof. Treat higher-scoring times as worth "
              "investigating further (family memory, hospital records) rather than a final answer. "
              "Ties or closely-clustered scores mean these events didn't discriminate strongly within "
              "this range — more events, or events closer to the uncertain window, would sharpen it."]
    return "\n".join(lines) + "\n"


def _birth_from_args(name, date, lat, lon, tz, city, house_system):
    y, mo, d = (int(x) for x in date.split("-"))
    return {"name": name, "year": y, "month": mo, "day": d,
            "lat": lat, "lon": lon, "tz": tz, "city": city, "house_system": house_system}


def _parse_events(raw_events: list) -> list:
    events = []
    for raw in raw_events:
        date_part, sep, label = raw.partition(":")
        if not sep:
            raise ValueError(f"--event {raw!r} must be YYYY-MM-DD:label")
        events.append({"date": date_part.strip(), "label": label.strip() or date_part.strip()})
    return events


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Lightweight birth-time rectification via kerykeion.")
    ap.add_argument("--name", default="Chart")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--time-start", required=True, help="HH:MM")
    ap.add_argument("--time-end", required=True, help="HH:MM")
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--tz", required=True)
    ap.add_argument("--city", default="")
    ap.add_argument("--house-system", default="Placidus")
    ap.add_argument("--event", action="append", default=[],
                    help="YYYY-MM-DD:label — a dated life event; repeatable, at least one required")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    try:
        if not args.event:
            raise ValueError("at least one --event YYYY-MM-DD:label is required")
        events = _parse_events(args.event)
        birth = _birth_from_args(args.name, args.date, args.lat, args.lon, args.tz,
                                 args.city, args.house_system)
        result = analyze(birth, args.time_start, args.time_end, events)
    except Exception as e:  # noqa: BLE001 — clean message, no traceback
        print(f"Error: {e}", file=sys.stderr)
        return 1

    report = render_markdown(result, birth, args.time_start, args.time_end, events)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Wrote {args.out}. Keep it private.")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
