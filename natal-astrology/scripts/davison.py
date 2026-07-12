"""Route A relationship charts: Davison (time-space midpoint) + Marks (per-person POV).

Reuses helpers from chart.py and synastry.py. Input: two birth dicts (same shape as
chart.build_chart_data). CLI: JSON payload on stdin, e.g.
  {"birth_a":{...},"birth_b":{...},"target":"davison|composite|marks","marks_mode":"natal_davison"}
"""
import argparse
import json
import sys
from datetime import datetime

import pytz

from chart import SIGNS
from synastry import (_person, _aspect, find_house, PLANET_NAMES, CROSS_BODIES,
                      build_synastry_data)


def _to_utc(birth: dict) -> datetime:
    naive = datetime(birth["year"], birth["month"], birth["day"], birth["hour"], birth["minute"])
    tz = birth.get("tz", "UTC")
    zone = pytz.utc if tz == "UTC" else pytz.timezone(tz)
    return zone.localize(naive).astimezone(pytz.utc)


def davison_birth(b1: dict, b2: dict, name: str = "Davison", house_system: str = "Placidus") -> dict:
    u1, u2 = _to_utc(b1), _to_utc(b2)
    mid = u1 + (u2 - u1) / 2
    # NOTE: simple mean of lat/lon; antimeridian pairs (e.g. lon 170 & -170) average to the wrong
    # hemisphere — known, deferred (rare for real birth pairs).
    return {"name": name, "year": mid.year, "month": mid.month, "day": mid.day,
            "hour": mid.hour, "minute": mid.minute,
            "lat": (b1["lat"] + b2["lat"]) / 2, "lon": (b1["lon"] + b2["lon"]) / 2,
            "tz": "UTC", "city": "", "house_system": house_system}


def _chart_from_person(person: dict, meta: dict) -> dict:
    bodies = person["bodies"]
    planets = [{"body": n, "sign": bodies[n]["sign"], "degree": bodies[n]["degree"],
                "house": bodies[n]["house"], "retrograde": bodies[n]["retro"]} for n in PLANET_NAMES]
    angles = {"ASC": {"sign": bodies["ASC"]["sign"], "degree": bodies["ASC"]["degree"]},
              "MC": {"sign": bodies["MC"]["sign"], "degree": bodies["MC"]["degree"]}}
    names = [n for n in CROSS_BODIES if n in bodies]
    aspects = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            res = _aspect(bodies[names[i]]["abs"] - bodies[names[j]]["abs"])
            if res:
                aspects.append({"a": names[i], "type": res[0], "b": names[j], "orb": res[1]})
    return {"meta": meta, "planets": planets, "angles": angles,
            "cusps": [round(c, 2) for c in person["cusps"]], "aspects": aspects}


def _davison_meta(db: dict, source: str) -> dict:
    return {"datetime_utc": f"{db['year']:04d}-{db['month']:02d}-{db['day']:02d}"
                            f"T{db['hour']:02d}:{db['minute']:02d}Z",
            "lat": round(db["lat"], 4), "lon": round(db["lon"], 4), "source": source}


def build_davison(b1: dict, b2: dict) -> dict:
    db = davison_birth(b1, b2)
    return _chart_from_person(_person(db), _davison_meta(db, "davison(A,B)"))


def _composite_target(b1: dict, b2: dict) -> dict:
    comp = build_synastry_data(b1, b2)["composite"]
    bodies = {}
    for p in comp["planets"]:
        bodies[p["body"]] = {"abs": SIGNS.index(p["sign"]) * 30 + p["degree"]}
    for ang in ("ASC", "MC"):
        a = comp["angles"][ang]
        bodies[ang] = {"abs": SIGNS.index(a["sign"]) * 30 + a["degree"]}
    asc_idx = SIGNS.index(comp["angles"]["ASC"]["sign"])
    cusps = [((asc_idx + k) % 12) * 30 for k in range(12)]   # whole-sign cusps from composite ASC
    return {"bodies": bodies, "cusps": cusps}


def _comparison(natal: dict, target: dict) -> dict:
    inter = []
    for nn in CROSS_BODIES:
        if nn not in natal["bodies"]:
            continue
        for rn in CROSS_BODIES:
            if rn not in target["bodies"]:
                continue
            res = _aspect(natal["bodies"][nn]["abs"] - target["bodies"][rn]["abs"])
            if res:
                inter.append({"a": f"N.{nn}", "type": res[0], "b": f"R.{rn}", "orb": res[1]})
    overlays = [{"planet": f"N.{n}", "house": find_house(natal["bodies"][n]["abs"], target["cusps"])}
                for n in PLANET_NAMES]
    return {"inter_aspects": inter, "overlays": overlays}


def build_marks(b1: dict, b2: dict, mode: str = "natal_davison") -> dict:
    if mode == "canonical":
        dav1 = davison_birth(b1, b2)
        da, db_ = davison_birth(dav1, b1), davison_birth(dav1, b2)
        return {"mode": mode,
                "a": _chart_from_person(_person(da), _davison_meta(da, "davison(davison(A,B), A)")),
                "b": _chart_from_person(_person(db_), _davison_meta(db_, "davison(davison(A,B), B)"))}
    if mode == "natal_davison":
        target = _person(davison_birth(b1, b2))
    elif mode == "natal_composite":
        target = _composite_target(b1, b2)
    else:
        raise ValueError(f"Unknown Marks mode {mode!r}. Use natal_composite|natal_davison|canonical.")
    return {"mode": mode, "a": _comparison(_person(b1), target), "b": _comparison(_person(b2), target)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Davison / Marks / composite from two births (JSON on stdin).")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    try:
        payload = json.load(sys.stdin)
        a, b = payload["birth_a"], payload["birth_b"]
        target = payload.get("target", "davison")
        if target == "davison":
            out = build_davison(a, b)
        elif target == "composite":
            out = build_synastry_data(a, b)["composite"]
        elif target == "marks":
            out = build_marks(a, b, payload.get("marks_mode", "natal_davison"))
        else:
            raise ValueError(f"Unknown target {target!r}. Use davison|composite|marks.")
    except Exception as e:  # noqa: BLE001 — clean message, no traceback
        print(f"Error: {e}", file=sys.stderr)
        return 1
    text = json.dumps(out, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Wrote {args.out}. Keep birth data private.")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
