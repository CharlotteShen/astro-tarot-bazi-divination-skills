# Chart wheels (SVG images) — v1.1.4

On-request SVG wheels rendered by kerykeion (Route A). Never auto-generated with a reading; produce one
only when the user asks ("show my chart wheel", "画个星盘", "draw our synastry wheel").

## Requirements
- **Route A only.** A wheel is computed from birth date/time/place (kerykeion recomputes the chart).
  A Route-B "positions only" paste cannot be drawn — ask the user for date/time/place first.
- The `birth-data.md` meta block already carries `date/time/lat/lon/tz/city` when present; pass those to
  `scripts/wheel.py`.

## Types (`--type`)
- `natal` — one person.
- `synastry` — two charts overlaid (bi-wheel).
- `composite` — kerykeion's native midpoint composite.
- `davison` — the Davison time-space midpoint chart (drawn as a single chart).
- `marks` — the canonical Marks chart (Davison-of-Davison), per person; `--who A|B`.

## Options
- `--theme light` (default) `| dark | classic`.
- `--lang EN` (default) `| CN` (follow the reading language).
- `--out-dir` — defaults to `natal-astrology/charts/` (**gitignored** — a wheel reveals the birth chart).

## Consistency & caveats
- Wheels draw **our** five major aspects with our orbs (conj/opp/sq/tri 8°, sextile 6°) and our point set
  (10 planets + North Node + Chiron + ASC/MC), so the lines match the text reading.
- The **composite** wheel uses kerykeion's native composite, which can differ by a fraction of a degree
  from `synastry.py`'s computed composite — fine for an illustrative image.
- **Unknown birth time:** compute at a labeled local-noon (12:00); tell the user the Ascendant, MC,
  houses, and exact Moon degree in the image are placeholders. Never present a noon wheel as the real chart.

## Example
```
natal-astrology/scripts/.venv/bin/python natal-astrology/scripts/wheel.py \
  --type natal --name ABC --date 2000-01-01 --time 12:00 \
  --lat 51.5074 --lon -0.1278 --tz Europe/London --city London --theme light
```
Prints the saved path, e.g. `natal-astrology/charts/natal-abc-light.svg`.

## 中文 terms
星盘图 chart wheel · 合盘图 synastry wheel · 组合中点盘 composite · 时空中点盘 Davison · 马克思盘 Marks
