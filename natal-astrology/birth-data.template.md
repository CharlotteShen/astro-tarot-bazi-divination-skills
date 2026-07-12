# Birth Data

<!-- HOW TO USE: Copy this file to `birth-data.md` (kept private, gitignored) and fill it in.
     Fill it from astro.com (see references/data-contract.md → "Route B"), or run
     `python scripts/chart.py` to generate it automatically. Keep all field names unchanged. -->

## Meta
- name: 
- date:            <!-- YYYY-MM-DD -->
- time:            <!-- HH:MM, 24-hour -->
- time_range:      <!-- optional, HH:MM-HH:MM. Only if the exact time is unknown but a window is known
                        (e.g. 06:00-09:00). Does NOT replace `time` — leave `time` as your best guess
                        or "unknown". Powers the birth-time sensitivity report (references/sensitivity.md). -->
- location:        <!-- City, Country -->
- lat:             <!-- signed decimal degrees, no N/S letter: North +, South −. e.g. Beijing 39.90, Sydney -33.87 -->
- lon:             <!-- signed decimal degrees, no E/W letter: East +, West −. e.g. Beijing 116.41, New York -74.01 -->
- tz:              <!-- e.g. Asia/Shanghai or +08:00 -->
- house_system: Placidus
- zodiac: tropical
- source:          <!-- astro.com | kerykeion | manual -->
- language: en     <!-- en or zh; this is your DEFAULT output language -->
- gender:          <!-- she/her | he/him | they/them | other — used for correct pronouns; never assumed from name -->
- bazi_gender:     <!-- 男 | 女 — 八字大运顺逆用（阳男阴女顺排）；与上面的代词字段无关，可留空，用到时会问 -->

## Planets
<!-- sign | degree within the sign, decimal 0–30, 1–2 places is plenty
     (astro.com shows e.g. 24°51′ → convert: 24 + 51/60 ≈ 24.85, drop seconds) | house (1-12) | retrograde (yes/no) -->
- Sun:      sign=         degree=        house=      retrograde=
- Moon:     sign=         degree=        house=      retrograde=
- Mercury:  sign=         degree=        house=      retrograde=
- Venus:    sign=         degree=        house=      retrograde=
- Mars:     sign=         degree=        house=      retrograde=
- Jupiter:  sign=         degree=        house=      retrograde=
- Saturn:   sign=         degree=        house=      retrograde=
- Uranus:   sign=         degree=        house=      retrograde=
- Neptune:  sign=         degree=        house=      retrograde=
- Pluto:    sign=         degree=        house=      retrograde=

## Angles
- ASC: sign=         degree=
- MC:  sign=         degree=

## Points
<!-- North Node: use astro.com's "True Node" value (matches the script; not "Mean Node").
     South Node isn't needed — it's the exact opposite sign/degree. Nodes are normally retrograde → yes. -->
- North Node: sign=         degree=        house=      retrograde=
- Chiron:     sign=         degree=        house=      retrograde=

## Aspects
<!-- one per line: BodyA aspect BodyB (orb) ; aspect ∈ conjunction/sextile/square/trine/opposition
     Minimum: aspects among the 10 planets. Better: also include aspects to ASC/MC if listed. Node/Chiron optional. -->
- 
- 

## Balance (optional — derivable)
- elements: fire=   earth=   air=   water=
- modalities: cardinal=   fixed=   mutable=

## END OF FILE CONTENT
