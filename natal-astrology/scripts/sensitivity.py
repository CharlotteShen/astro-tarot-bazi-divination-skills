"""Route A birth-time sensitivity report: which chart factors are stable vs. flip within an
uncertain birth-time range, with exact flip minutes pinpointed via coarse-scan + bisection.
"""
import argparse
import sys
from datetime import datetime, timedelta

from chart import SIGNS, build_chart_data, _ang_dist

PLANET_NAMES = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
                "Uranus", "Neptune", "Pluto"]

# --- v1.1.5 sensitivity tuning (own conventions — adjust freely) ---
COARSE_STEP_MINUTES = 15   # safe: the fastest tracked factor (angle-orb entry/exit) needs ~48min
BISECT_TOLERANCE_MINUTES = 1
ANGLE_ORB = 6.0            # ° — same "planets on angles" convention as reading-method.md


def _abs(sign, degree):
    return SIGNS.index(sign) * 30 + degree


def _snapshot(birth: dict) -> dict:
    cd = build_chart_data(birth)
    snap = {}

    asc, mc = cd["angles"]["ASC"], cd["angles"]["MC"]
    snap["ASC_sign"] = asc["sign"]
    snap["MC_sign"] = mc["sign"]
    asc_abs = _abs(asc["sign"], asc["degree"])
    mc_abs = _abs(mc["sign"], mc["degree"])

    by_name = {p["body"]: p for p in cd["planets"]}
    for name in PLANET_NAMES:
        p = by_name[name]
        snap[f"house_{name}"] = p["house"]
        p_abs = _abs(p["sign"], p["degree"])
        snap[f"onangle_{name}_ASC"] = _ang_dist(p_abs, asc_abs) <= ANGLE_ORB
        snap[f"onangle_{name}_MC"] = _ang_dist(p_abs, mc_abs) <= ANGLE_ORB

    snap["Moon_sign"] = by_name["Moon"]["sign"]
    snap["sect"] = cd["enrichment"]["sect"]

    for lot in ("fortune", "spirit", "eros"):
        lot_point = cd["enrichment"]["lots"][lot]
        snap[f"lot_{lot}_sign"] = lot_point["sign"]
        snap[f"lot_{lot}_house"] = lot_point["house"]

    vertex = cd["enrichment"]["vertex"]
    snap["vertex_sign"] = vertex["sign"] if vertex else None
    snap["vertex_house"] = vertex["house"] if vertex else None

    sun_moon = cd["enrichment"]["midpoints"]["sun_moon"]
    snap["sunmoon_sign"] = sun_moon["sign"]
    snap["sunmoon_house"] = sun_moon["house"]

    return snap


def _birth_at_offset(birth: dict, base_dt: datetime, offset_minutes: int) -> dict:
    dt = base_dt + timedelta(minutes=offset_minutes)
    return dict(birth, year=dt.year, month=dt.month, day=dt.day, hour=dt.hour, minute=dt.minute)


def _range_offsets(birth: dict, start: str, end: str, step_minutes: int):
    sh, sm = (int(x) for x in start.split(":"))
    eh, em = (int(x) for x in end.split(":"))
    base_dt = datetime(birth["year"], birth["month"], birth["day"], sh, sm)
    end_dt = datetime(birth["year"], birth["month"], birth["day"], eh, em)
    if end_dt < base_dt:
        end_dt += timedelta(days=1)
    total_minutes = int((end_dt - base_dt).total_seconds() // 60)
    offsets = list(range(0, total_minutes + 1, step_minutes))
    if offsets[-1] != total_minutes:
        offsets.append(total_minutes)
    return base_dt, offsets


def _bisect_flip(birth: dict, base_dt: datetime, lo: int, hi: int, key: str, lo_val) -> int:
    while hi - lo > BISECT_TOLERANCE_MINUTES:
        mid = (lo + hi) // 2
        val = _snapshot(_birth_at_offset(birth, base_dt, mid))[key]
        if val == lo_val:
            lo = mid
        else:
            hi = mid
    return hi


def analyze(birth: dict, start: str, end: str) -> dict:
    base_dt, offsets = _range_offsets(birth, start, end, COARSE_STEP_MINUTES)
    samples = [(off, _snapshot(_birth_at_offset(birth, base_dt, off))) for off in offsets]
    keys = samples[0][1].keys()

    stable, sensitive = {}, {}
    for key in keys:
        segments = [samples[0][1][key]]
        flip_times = []
        for i in range(len(samples) - 1):
            off_lo, snap_lo = samples[i]
            off_hi, snap_hi = samples[i + 1]
            if snap_lo[key] != snap_hi[key]:
                flip_offset = _bisect_flip(birth, base_dt, off_lo, off_hi, key, snap_lo[key])
                flip_dt = base_dt + timedelta(minutes=flip_offset)
                flip_times.append(flip_dt.strftime("%H:%M"))
                segments.append(snap_hi[key])
        if not flip_times:
            stable[key] = segments[0]
        else:
            timeline = [{"value": v, "until": (flip_times[i] if i < len(flip_times) else None)}
                        for i, v in enumerate(segments)]
            sensitive[key] = timeline

    return {
        "stable": stable, "sensitive": sensitive,
        "meta": {"name": birth.get("name", ""),
                 "date": f"{birth['year']:04d}-{birth['month']:02d}-{birth['day']:02d}",
                 "start": start, "end": end,
                 "city": birth.get("city", ""), "tz": birth.get("tz", "")},
    }


LABELS = {
    "ASC_sign": "Ascendant", "MC_sign": "MC",
    "Moon_sign": "Moon sign", "sect": "Sect (day/night)",
    "lot_fortune_sign": "Part of Fortune (sign)", "lot_fortune_house": "Part of Fortune (house)",
    "lot_spirit_sign": "Part of Spirit (sign)", "lot_spirit_house": "Part of Spirit (house)",
    "lot_eros_sign": "Part of Eros (sign)", "lot_eros_house": "Part of Eros (house)",
    "vertex_sign": "Vertex (sign)", "vertex_house": "Vertex (house)",
    "sunmoon_sign": "Sun/Moon midpoint (sign)", "sunmoon_house": "Sun/Moon midpoint (house)",
}
for _name in PLANET_NAMES:
    LABELS[f"house_{_name}"] = f"{_name}'s house"
    LABELS[f"onangle_{_name}_ASC"] = f"{_name} conjunct Ascendant (±6°)"
    LABELS[f"onangle_{_name}_MC"] = f"{_name} conjunct MC (±6°)"


def render_markdown(result: dict, birth: dict, start: str, end: str) -> str:
    m = result["meta"]
    lines = [f"# Birth-time sensitivity report — {m['name']}", "",
             f"Range checked: {m['date']}, {start}–{end} ({m['city']}, {m['tz']})", "",
             "## Stable (same regardless of exact time within your range)"]
    for key, value in result["stable"].items():
        lines.append(f"- {LABELS.get(key, key)}: {value}")

    lines += ["", "## Sensitive (changes within your range)"]
    for key, timeline in result["sensitive"].items():
        parts = []
        for i, seg in enumerate(timeline):
            if seg["until"] is not None:
                parts.append(f"{seg['value']} (until {seg['until']})")
            else:
                prev_until = timeline[i - 1]["until"] if i > 0 else None
                parts.append(f"{seg['value']} (from {prev_until})" if prev_until
                             else f"{seg['value']}")
        lines.append(f"- {LABELS.get(key, key)}: " + " → ".join(parts))

    lines += ["", "## Takeaway"]
    if result["sensitive"]:
        sensitive_labels = ", ".join(LABELS.get(k, k) for k in list(result["sensitive"])[:5])
        lines.append(
            "Your stable placements above hold no matter the exact time in this range — a "
            f"reading can lean on those. But {sensitive_labels} depend on exactly when in this range "
            "you were born; narrowing the time (or getting the exact time) would make those "
            "trustworthy too.")
    else:
        lines.append(
            "Everything checked is stable across this entire range — this window is precise "
            "enough for a full reading already.")
    return "\n".join(lines) + "\n"


def _birth_from_args(name, date, lat, lon, tz, city, house_system):
    y, mo, d = (int(x) for x in date.split("-"))
    return {"name": name, "year": y, "month": mo, "day": d,
            "lat": lat, "lon": lon, "tz": tz, "city": city, "house_system": house_system}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Birth-time sensitivity report via kerykeion.")
    ap.add_argument("--name", default="Chart")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--time-start", required=True, help="HH:MM")
    ap.add_argument("--time-end", required=True, help="HH:MM")
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--tz", required=True)
    ap.add_argument("--city", default="")
    ap.add_argument("--house-system", default="Placidus")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    try:
        birth = _birth_from_args(args.name, args.date, args.lat, args.lon, args.tz,
                                 args.city, args.house_system)
        result = analyze(birth, args.time_start, args.time_end)
    except Exception as e:  # noqa: BLE001 — clean message, no traceback
        print(f"Error: {e}", file=sys.stderr)
        return 1

    report = render_markdown(result, birth, args.time_start, args.time_end)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Wrote {args.out}. Keep it private.")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
