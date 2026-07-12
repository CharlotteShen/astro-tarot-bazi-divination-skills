"""Route A chart-wheel images: render SVG wheels via kerykeion.

Renders natal / synastry / composite / davison / marks wheels. Reuses _subject from
chart.py and davison_birth from davison.py so the wheel matches the reading's numbers.
Aspect lines use our own orbs/points (5 majors), not kerykeion's defaults.
"""
import argparse
import os
import re
import sys

from chart import _subject

# Our reading's bodies + angles (kerykeion Literal names). No Lilith/South Node.
ACTIVE_POINTS = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
                 "Uranus", "Neptune", "Pluto", "Mean_Node", "Chiron",
                 "Ascendant", "Medium_Coeli"]
# Our five majors + our orbs (kerykeion defaults use square-orb 5 and add quintile).
ACTIVE_ASPECTS = [{"name": "conjunction", "orb": 8}, {"name": "opposition", "orb": 8},
                  {"name": "square", "orb": 8}, {"name": "trine", "orb": 8},
                  {"name": "sextile", "orb": 6}]

DEFAULT_OUT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "charts"))

TYPES = ("natal", "synastry", "composite", "davison", "marks")


def _svg(first, chart_type, second=None, theme="light", lang="EN"):
    from kerykeion import KerykeionChartSVG
    chart = KerykeionChartSVG(
        first, chart_type, second, theme=theme, chart_language=lang,
        active_points=ACTIVE_POINTS, active_aspects=ACTIVE_ASPECTS,
    )
    return chart.makeTemplate()


def build_wheel(chart_type, birth, birth2=None, who="A", theme="light", lang="EN"):
    ct = chart_type.lower()
    if ct not in TYPES:
        raise ValueError(f"Unknown chart type {chart_type!r}. Use {'|'.join(TYPES)}.")
    if ct != "natal" and birth2 is None:
        raise ValueError(f"chart type {ct!r} needs a second person (birth2).")

    if ct == "natal":
        return _svg(_subject(birth), "Natal", theme=theme, lang=lang)
    if ct == "synastry":
        return _svg(_subject(birth), "Synastry", _subject(birth2), theme=theme, lang=lang)
    if ct == "composite":
        from kerykeion import CompositeSubjectFactory
        model = CompositeSubjectFactory(
            _subject(birth), _subject(birth2)).get_midpoint_composite_subject_model()
        return _svg(model, "Composite", theme=theme, lang=lang)
    if ct == "davison":
        from davison import davison_birth
        hs = birth.get("house_system") or "Placidus"
        return _svg(_subject(davison_birth(birth, birth2, house_system=hs)), "Natal",
                    theme=theme, lang=lang)
    # ct == "marks": canonical Davison-of-Davison, per-person POV
    from davison import davison_birth
    dav1 = davison_birth(birth, birth2)
    who_u = who.upper()
    if who_u not in ("A", "B"):
        raise ValueError(f"who must be 'A' or 'B', got {who!r}.")
    inner = birth if who_u == "A" else birth2
    hs = birth.get("house_system") or "Placidus"
    marks_birth = davison_birth(dav1, inner, name=f"Marks {who_u}", house_system=hs)
    return _svg(_subject(marks_birth), "Natal", theme=theme, lang=lang)


def _slug(s):
    s = (s or "").strip().lower().replace(" ", "-")
    return re.sub(r"[^a-z0-9\-]", "", s) or "chart"


def _filename(chart_type, birth, birth2, who, theme, lang):
    ct = chart_type.lower()
    a = _slug(birth.get("name", "chart"))
    suffix = f"-{theme}" + ("-cn" if lang.upper() == "CN" else "")
    if ct == "natal":
        base = f"natal-{a}"
    elif ct == "marks":
        base = f"marks-{who.lower()}-{a}-{_slug(birth2.get('name', 'b'))}"
    else:  # synastry, composite, davison
        base = f"{ct}-{a}-{_slug(birth2.get('name', 'b'))}"
    return f"{base}{suffix}.svg"


def render_to_file(chart_type, birth, birth2=None, who="A", theme="light", lang="EN",
                   out_dir=None):
    svg = build_wheel(chart_type, birth, birth2, who=who, theme=theme, lang=lang)
    out_dir = out_dir or DEFAULT_OUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, _filename(chart_type, birth, birth2, who, theme, lang))
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return path


def _birth_from_args(name, date, time, lat, lon, tz, city, house_system):
    y, mo, d = (int(x) for x in date.split("-"))
    hh, mm = (int(x) for x in time.split(":"))
    return {"name": name, "year": y, "month": mo, "day": d, "hour": hh, "minute": mm,
            "lat": lat, "lon": lon, "tz": tz, "city": city, "house_system": house_system}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Render an SVG chart wheel via kerykeion.")
    ap.add_argument("--type", required=True, choices=list(TYPES))
    ap.add_argument("--who", default="A", choices=["A", "B"])
    ap.add_argument("--theme", default="light", choices=["light", "dark", "classic"])
    ap.add_argument("--lang", default="EN", choices=["EN", "CN"])
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--house-system", default="Placidus")
    ap.add_argument("--name", default="A")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--time", required=True, help="HH:MM")
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--tz", required=True)
    ap.add_argument("--city", default="")
    ap.add_argument("--name2", default="B")
    ap.add_argument("--date2")
    ap.add_argument("--time2")
    ap.add_argument("--lat2", type=float)
    ap.add_argument("--lon2", type=float)
    ap.add_argument("--tz2")
    ap.add_argument("--city2", default="")
    args = ap.parse_args(argv)

    try:
        birth = _birth_from_args(args.name, args.date, args.time, args.lat, args.lon,
                                 args.tz, args.city, args.house_system)
        birth2 = None
        if args.type != "natal":
            if not (args.date2 and args.time2 and args.lat2 is not None
                    and args.lon2 is not None and args.tz2):
                raise ValueError(
                    f"--type {args.type} needs person B "
                    f"(--date2/--time2/--lat2/--lon2/--tz2).")
            birth2 = _birth_from_args(args.name2, args.date2, args.time2, args.lat2,
                                      args.lon2, args.tz2, args.city2, args.house_system)
        path = render_to_file(args.type, birth, birth2, who=args.who, theme=args.theme,
                              lang=args.lang, out_dir=args.out_dir)
    except Exception as e:  # noqa: BLE001 — clean message, no traceback
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
