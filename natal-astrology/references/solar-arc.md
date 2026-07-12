# Solar arc directions — v1.3.4

Every natal point — all ten planets AND the angles — is advanced by the **same arc**: the exact distance
the secondary-progressed Sun has traveled since birth (~1° per year of life). Directed points aspecting
natal points mark years when that pairing "arrives". Completes the predictive line (transits = outer
weather · Solar Return = the year's chart · profections = the year's emphasis · progressions = inner
development · solar arc = the whole chart advancing as one).

## The technique
- **Arc:** exact progressed-Sun arc (day-for-a-year at 365.25 — the same sourced convention as
  `references/progressions.md`), not the 1°/year approximation. The actual rate (~0.96–1.02°/yr,
  seasonal) is computed and used for timing.
- **Contacts:** each directed point vs every natal planet/angle (self-pairs excluded), five majors at a
  **1° orb**. Traditional directions practice emphasizes hard aspects (conjunction/square/opposition) —
  we keep the project-wide five-majors convention and note the tradition here; weight hard contacts more
  heavily in a reading.
- **Timing:** because everything moves at the arc rate, orb converts to time — each contact reports
  "applying — exact in ~X months" or "separating — exact ~X months ago" (approximate to ~a month).
- **Whole-chart years:** when the arc itself is within 1° of a major aspect angle (e.g. ~60 at age ~59),
  the entire directed chart aspects its own natal positions — reported as a one-line note.

## Reliability
The arc is robust even with an unknown birth time (natal Sun ±12h ≈ ±0.5° ≈ ±6 months of timing,
flagged). Directed ASC/MC and contacts **to** the natal ASC/MC require a known birth time.

## Usage
```
natal-astrology/scripts/.venv/bin/python natal-astrology/scripts/solar_arc.py \
  --name ABC --date 2000-01-01 --time 12:00 \
  --lat 51.5074 --lon -0.1278 --tz Europe/London --city London \
  --on 2026-07-02
```
`--on` defaults to today. Omit `--time` if the birth time is unknown (flagged). Without `--out`, prints
to stdout; with `--out`, writes markdown to that path.

## Output & privacy
Reveals the natal chart + timing — personal. Default output (when saved):
`natal-astrology/solar-arc-reports/` — **gitignored**.

## 中文 terms
太阳弧推运 solar arc directions · 推进点 directed point · 入相位/出相位 applying/separating.
Timing is a window, not a promised event.
