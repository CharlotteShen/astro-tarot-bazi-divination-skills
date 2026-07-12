"""Route A annual & monthly profections: the Hellenistic time-lord technique (age -> profected house,
sign, lord of the year) plus the monthly sub-cycle. Pure arithmetic on the natal rising sign + birth
date; reuses chart.py only for the natal chart. Traditional 7-classical rulerships.
"""
import argparse
import sys
from datetime import date, timedelta

from chart import build_chart_data, SIGNS

TRAD_RULER = {"Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
              "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
              "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn",
              "Pisces": "Jupiter"}
YEAR_DAYS = 365.25


def _ord(n: int) -> str:
    suffix = "th" if 11 <= n % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _age_on(birth_date: date, ref_date: date) -> int:
    return (ref_date.year - birth_date.year
            - ((ref_date.month, ref_date.day) < (birth_date.month, birth_date.day)))


def _birthday_in_year(year: int, bmonth: int, bday: int) -> date:
    try:
        return date(year, bmonth, bday)
    except ValueError:   # Feb 29 in a non-leap year
        return date(year, 2, 28)


def _most_recent_birthday(bmonth: int, bday: int, ref_date: date) -> date:
    this = _birthday_in_year(ref_date.year, bmonth, bday)
    return this if this <= ref_date else _birthday_in_year(ref_date.year - 1, bmonth, bday)


def annual_profection(rising_sign: str, age: int) -> dict:
    house = (age % 12) + 1
    sign = SIGNS[(SIGNS.index(rising_sign) + house - 1) % 12]
    return {"house": house, "sign": sign, "lord": TRAD_RULER[sign]}


def monthly_profection(rising_sign: str, annual_house: int, month_index: int) -> dict:
    house = ((annual_house - 1) + month_index) % 12 + 1
    sign = SIGNS[(SIGNS.index(rising_sign) + house - 1) % 12]
    return {"house": house, "sign": sign, "lord": TRAD_RULER[sign]}


def build_profections(natal_birth: dict, ref_date: date) -> dict:
    natal_cd = build_chart_data(natal_birth)
    rising = natal_cd["angles"]["ASC"]["sign"]
    birth_time_known = natal_birth.get("time_known", True)
    bmonth, bday = natal_birth["month"], natal_birth["day"]
    birth_date = date(natal_birth["year"], bmonth, bday)
    age = _age_on(birth_date, ref_date)

    annual = annual_profection(rising, age)
    lord_placement = next(((p["sign"], p["house"]) for p in natal_cd["planets"]
                           if p["body"] == annual["lord"]), None)
    activated = [p["body"] for p in natal_cd["planets"] if p["sign"] == annual["sign"]]

    mr = _most_recent_birthday(bmonth, bday, ref_date)
    seg = YEAR_DAYS / 12
    month_index = min(int((ref_date - mr).days // seg), 11)
    monthly = monthly_profection(rising, annual["house"], month_index)
    monthly["month_index"] = month_index
    monthly["start"] = mr + timedelta(days=round(month_index * seg))
    monthly["end"] = mr + timedelta(days=round((month_index + 1) * seg))

    return {
        "ref_date": ref_date,
        "year_window": (mr, _birthday_in_year(mr.year + 1, bmonth, bday)),
        "annual": {**annual, "lord_placement": lord_placement, "activated": activated},
        "monthly": monthly,
        "meta": {"name": natal_birth.get("name", ""), "rising": rising, "age": age,
                 "birth_time_known": birth_time_known},
    }


def render_markdown(result: dict) -> str:
    m, a, mo = result["meta"], result["annual"], result["monthly"]
    yw = result["year_window"]
    lines = [f"# Annual Profection — {m['name']} (as of {result['ref_date'].isoformat()})", "",
             f"Age {m['age']} · rising {m['rising']} · profection year "
             f"{yw[0].isoformat()} → {yw[1].isoformat()}", "",
             "## This year (annual profection)",
             f"- Profected house: {_ord(a['house'])} · sign: {a['sign']} · lord of the year: {a['lord']}"]
    if a["lord_placement"]:
        ls, lh = a["lord_placement"]
        lines.append(f"- Lord of the year ({a['lord']}) natally: {ls}, natal {_ord(lh)} house")
    lines.append(f"- Natal planets activated (in {a['sign']}): "
                 + (", ".join(a["activated"]) if a["activated"] else "(none)"))

    lines += ["", "## This month (monthly profection)",
              f"- {mo['start'].isoformat()} → {mo['end'].isoformat()}: {_ord(mo['house'])}-house month "
              f"· sign {mo['sign']} · month-lord {mo['lord']}",
              "", "## Notes",
              f"Watch the lord of the year ({a['lord']}) — its transits and its condition in your Solar "
              "Return colour the year."]
    if not m["birth_time_known"]:
        lines.append("Birth time unknown → only the profected house number (from your age) is reliable; "
                     "the profected sign, lord, and activations depend on the rising sign and are not.")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Annual & monthly profections via kerykeion.")
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
        result = build_profections(natal, ref)
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
