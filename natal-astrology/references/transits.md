# Transit snapshot — v1.2.0

On-request snapshot of which transiting bodies are aspecting the natal chart on a given date (default:
today), each with its orb and whether it's **applying** (tightening toward exact) or **separating**.
This is a snapshot of "what's active now", NOT forecasting — exact perfection dates, upcoming transits,
and retrograde multi-passes are a later version (v1.2.1).

## Requirements
- **Route A only.** Needs the natal chart computed plus transiting positions on the date.

## Movers and targets
- **Movers (12):** transiting Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto,
  Chiron, North Node — at **noon** on the snapshot date.
- **Targets:** natal 10 planets + Chiron + North Node, plus natal Ascendant + MC **when the birth time
  is known**. If the natal birth time is unknown, ASC/MC targets are omitted (see Reliability).

## Orbs (tighter than the rest of the skill — transit convention)
- Conjunction/opposition/square/trine **3°**, sextile **2°** (`TRANSIT_ASPECTS`).
- The transiting **Moon** gets **+2°** (`MOON_ORB_BONUS`) since it moves ~13°/day.

## Applying vs separating
For each active aspect, the orb on the snapshot date is compared to the orb one day later: smaller
tomorrow → applying, else separating.

## Reliability
- **Birth time known:** all targets active; report fully usable.
- **Birth time unknown:** natal chart at labeled noon; transits to ASC/MC are omitted and noted;
  natal-Moon-as-target hits are approximate.
- The transiting **Moon** is always noon-approximate (the snapshot date has no clock time).

## Usage
```
natal-astrology/scripts/.venv/bin/python natal-astrology/scripts/transits.py \
  --name ABC --date 2000-01-01 --time 12:00 \
  --lat 51.5074 --lon -0.1278 --tz Europe/London --city London \
  --on 2026-07-01
```
`--on` defaults to today. Omit `--time` if the birth time is unknown (angles are then suppressed).
Without `--out`, the report prints to stdout; with `--out`, it writes to that path.

## Output & privacy
Reveals the natal chart + a date's activity — personal. Default output location (when saved):
`natal-astrology/transit-reports/` — **gitignored**.

## Validation
Positions were cross-checked against **NASA JPL Horizons** (independent of Swiss Ephemeris): our
transiting longitudes for 2026-07-01 00:00 UT matched to arcseconds (Mars ~5″, Uranus ~9″, Saturn ~11″).
Since aspect/orb detection is deterministic on those positions, the snapshot is accurate; the natal-chart
path was also verified vs astro.com to ≤0.01° in v1.1.3.

## 中文 terms
行运/流年 transits · 入相位 applying · 出相位 separating · 本命 natal · 快行星/慢行星 fast/slow planets.
This is a snapshot, not forecasting.
