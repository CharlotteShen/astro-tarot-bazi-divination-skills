# Data Contract — natal chart data

This skill never computes positions. Chart data comes from Route A (the `chart.py` script) or
Route B (paste from astro.com) and is stored in the user's `birth-data.md` file. Both routes
populate the SAME fields below.

## Canonical fields

- **meta**: `name` (optional), `date` (YYYY-MM-DD), `time` (HH:MM, 24h), `location` (City, Country),
  `lat` (signed decimal degrees, North +/South −), `lon` (signed decimal degrees, East +/West −),
  `tz` (IANA name or UTC offset), `house_system` (default Placidus),
  `zodiac` (default tropical), `source` (kerykeion | astro.com | manual), `language` (en | zh, default en),
  `gender` (she/her | he/him | they/them | other — used for correct pronouns; never assumed from name).
- **time_range** (optional): `HH:MM-HH:MM` — present when the exact time is unknown but a window is
  known (v1.1.5). Informational only: readings/wheels still use the existing noon-placeholder
  convention (below) regardless of whether `time_range` is present; it exists so the birth-time
  sensitivity report (`scripts/sensitivity.py`) can pick up an already-recorded window.
- **planets** (all 10 required): Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto.
  Each has: `sign`, `degree` (decimal 0–30 within the sign; 1–2 places is enough — astro.com's
  `24°51′` becomes `24.85`, drop seconds), `house` (1–12), `retrograde` (true/false).
- **angles** (required): ASC (`sign`, `degree`), MC (`sign`, `degree`).
- **points** (recommended): North Node, Chiron — each `sign`, `degree`, `house`, `retrograde`.
- **aspects** (required): a list of `{ a, type, b, orb }`, type ∈ {conjunction, sextile, square, trine, opposition}.
  Minimum = aspects among the 10 planets. Recommended = also include aspects to ASC/MC (high-value:
  planets on the angles are top signals). Node/Chiron aspects are optional. Omitting some is fine —
  the reading just won't comment on what isn't listed.
- **balance** (recommended): elements {fire, earth, air, water}; modalities {cardinal, fixed, mutable}.

## Data tiers (graceful degradation)

- **Tier 1 (required for a reading):** house system + zodiac; 10 planets; ASC + MC; aspects.
- **Tier 2 (recommended):** North Node, Chiron; element/modality balance.
- **Tier 3 (ignored in v1):** Lilith, Part of Fortune, asteroids, declinations, transits.

If Tier 1 is incomplete, ask the user for the missing pieces. If the user proceeds anyway, state
plainly that depth is reduced. NEVER fabricate a position or aspect.

## Route B — how to fill the file from astro.com

1. Go to https://www.astro.com → Free Horoscopes → "Extended Chart Selection".
2. Enter birth date, exact time, and birthplace. Chart type: "Natal Chart Wheel". House system:
   Placidus (default) unless the user wants another. Click "Click here to show the chart".
3. The wheel page shows only a compact legend. For the TEXT data, click **"Additional tables (PDF)"**
   above the chart — that PDF lists the **positions table** (each planet's sign + degree + house +
   R for retrograde), the **ASC/MC**, and the **aspect grid** as text. Map those into
   `birth-data.template.md`. (The user can also just hand the PDF to the agent to parse.)
4. Easier-to-copy alternative: **astro-seek.com** shows the same positions + aspect list in plain
   HTML tables that select-and-copy cleanly.
5. No-typing alternative: skip Route B and use the Route A script (`scripts/chart.py`).

## Validation rules (run after filling)

- Exactly 10 planets present; each: a valid zodiac sign, degree in [0, 30), house in [1, 12].
- ASC and MC present, each with a valid sign + degree.
- North Node retrograde = true is expected and normal (informational, not an error).
- Every aspect's `a` and `b` reference a body present in the file; `orb` ≤ ~10°.
- On any failure: confirm with the user. Never silently guess or auto-correct.

## File format

The canonical store is `birth-data.md` (the filled copy of `birth-data.template.md`). The Route-A
script may instead emit the same fields as JSON; the skill reads either Markdown or JSON.

---

# Synastry data (v1.1.0)

Two-chart comparison. Produced by `scripts/synastry.py` (Route A) or by pasting astro.com synastry +
composite tables (Route B). Canonical `synastry_data` shape:

```
relationship_type: romantic | friendship | family | work
person_a: { meta, planets[10], angles{ASC,MC}, points[North Node, Chiron], cusps[12 abs degrees] }
person_b: { same shape }
inter_aspects: [ { a: "A.<body>", type, b: "B.<body>", orb } ]   # a is person A's body, b person B's
overlays:
  a_in_b: [ { planet: "A.<planet>", house: <1-12 in B> } ]
  b_in_a: [ { planet: "B.<planet>", house: <1-12 in A> } ]
composite:
  planets[10]: { body, sign, degree, house }   # house = whole-sign from composite ASC
  angles: { ASC{sign,degree}, MC{sign,degree} }
  aspects: [ { a, type, b, orb } ]
```

## Computation rules
- **Bodies compared (inter-aspects):** the 10 planets + North Node + Chiron + ASC + MC, person A × person B.
- **Aspect classification:** five majors, same orbs as `aspects.md` (conjunction/opposition/square/trine ≤8°, sextile ≤6°), applied to the angular separation of absolute longitudes.
- **House overlays:** a planet's absolute longitude → which of the other person's 12 houses it falls in (by their cusps). Both directions. (The 10 planets only.)
- **Composite planet:** nearer midpoint of the two absolute longitudes:
  `diff = ((λB − λA + 540) mod 360) − 180; mid = (λA + diff/2) mod 360`. Same for ASC and MC.
- **Composite houses:** whole-sign from the composite Ascendant — a composite planet's house =
  `((planet_sign_index − composite_ASC_sign_index) mod 12) + 1`.
- **Composite aspects:** among the 10 composite planets, same orbs.

## Route B (paste from astro.com)
astro.com → Extended Chart Selection → choose the **Synastry**/partner chart and the **Composite**
chart; each has an **"Additional tables (PDF)"** link with positions, **house cusps**, and the
inter-aspect grid as text. Map them into `synastry_data`, or hand the PDFs to the agent to parse.
If house cusps are unavailable, overlays/composite degrade — fall back to inter-aspects only and say so.

## Validation
- Every inter-aspect's `a` starts with `A.` and `b` with `B.`; type is one of the five majors; orb ≤ ~8°.
- Overlays cover all 10 planets each direction; house ∈ [1,12].
- Composite has 10 planets + ASC + MC.
- On any failure: confirm with the user; never fabricate.

---

## Reinforced contacts (v1.1.2)
Derived from `inter_aspects` by `find_reinforced`; added to `synastry_data`:
```
double_whammies: [ { pair: [P, Q], aspects: [ {a,type,b,orb}, {a,type,b,orb} ] } ]   # reciprocal A.P–B.Q AND A.Q–B.P
focal_points:    [ { body: "A.<X>" | "B.<Y>", count: n, aspects: [ {a,type,b,orb}, … ] } ]   # a body in >= 2 inter-aspects
```
- **double_whammies** = "doubly-wired" themes (especially binding). **focal_points** = hotspots the
  other person lights up several ways. The reading leads with these.

# Davison & Marks data (v1.1.1)

Derived relationship charts computed locally from two births (no astro.com). Three things:

## Davison chart `davison`
```
davison:
  meta:    { datetime_utc, lat, lon, source: "davison(A,B)" }
  planets: [10] { body, sign, degree, house, retrograde }
  angles:  { ASC{sign,degree}, MC{sign,degree} }
  cusps:   [12 abs degrees]
  aspects: [ { a, type, b, orb } ]   # among the davison's own bodies
```
Computation: **datetime** = average of the two births' UTC instants; **location** = average of the two
lats and the two lons (simple mean); then cast a real chart. The result is a *birthlike* that can be
fed back into Davison (used by canonical Marks).

## Marks `marks` (per-person POV; selectable mode)
```
marks:
  mode: natal_composite | natal_davison | canonical    # default natal_davison
  a, b:
    # comparison modes (natal_composite | natal_davison):
    { inter_aspects: [ {a:"N.<body>", type, b:"R.<body>", orb} ],   # N.=natal, R.=relationship chart
      overlays:      [ {planet:"N.<planet>", house:<1-12 in R>} ] }
    # canonical mode: a full chart read like a natal
    { meta, planets[10], angles{ASC,MC}, cusps[12], aspects }
```
- **natal_davison** (default): compare each natal to the couple's Davison (inter-aspects + overlays in Davison's real houses).
- **natal_composite**: compare each natal to the composite (overlays use the composite's whole-sign houses from its ASC).
- **canonical**: Marks A = `Davison(Davison(A,B), A)`, Marks B = `Davison(Davison(A,B), B)` — read like natals.

## Standalone composite
No new shape — the v1.1.0 `composite` block can be requested and read on its own as the relationship entity.

## Birth-time handling (all charts)
If a birth time is unknown, compute with a **labeled local-noon (12:00) assumption** and flag the
**time-dependent** factors (Ascendant, MC, houses, exact Moon degree, and anything derived — overlays,
Davison/Marks angles & houses, composite ASC/houses). Time-robust planet positions/aspects stay usable.
Never present noon as the real birth time.

---

# Enrichment data (v1.1.3)

Added to natal `chart_data` (computed in `chart.py`):
```
enrichment:
  sect: day | night
  lots:        { fortune:{sign,degree,house}, spirit:{...}, eros:{...} }
  midpoints:   { sun_moon:{sign,degree,house}, occupied:[ {planet, of:[A,B], orb} ] }
  declinations:{ "<body>": <decimal degrees> }   # 10 planets + North Node + Chiron (best-effort)
  parallels:   [ {a, b, type: parallel | contra_parallel, orb} ]
  vertex:      { sign, degree, house }            # anti-vertex = opposite point
  asteroids:   { ceres:{sign,degree,house}, pallas:{...}, juno:{...}, vesta:{...} }   # v1.2.2
  black_moon_lilith: {sign,degree,house}                                             # v1.2.2, mean apogee
  asteroid_contacts: [ {a, type, b, orb} ]   # a=asteroid/Lilith name, b=natal planet/ASC/MC, orb ≤ 2°
```
Computation rules + sources: see the v1.1.3 design spec §5/§13 (declination/vertex via Swiss Ephemeris;
Hellenistic lot/sect formulas, verified). **Tunable conventions** (constants in `chart.py`):
`MIDPOINT_ORB = 1.5°`, `PARALLEL_ORB = 1.0°` — own choices, adjust freely.
