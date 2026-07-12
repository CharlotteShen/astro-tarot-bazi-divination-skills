# Solar Return — v1.3.0

The chart for the exact moment each year when the transiting Sun returns to its natal longitude (your
"astrological birthday"), read as a year-ahead chart — the SR chart itself plus a bridge onto your natal
chart. The first of the v1.3.x predictive line.

## Requirements
- **Route A only.** Needs the natal chart + a computed return moment. A known **natal birth time** is
  important: the return instant is derived from the natal Sun (which shifts ~2.5′/hour), so without a
  birth time the SR angles/houses/bridge are unreliable (flagged in the report).

## The return moment
The Sun never retrogrades, so it returns to its natal longitude exactly once per year, within ~a day of
the birthday. The tool scans the birthday ±2 days and pins the instant to the minute (SR Sun lands on the
natal Sun to arcseconds).

## Location (birth vs relocated)
- **Default:** cast at the birth location (traditional).
- **Relocated:** pass `--loc-lat/--loc-lon/--loc-tz/--loc-city` for where you'll actually be on your
  birthday. Only the angles/houses change; the SR planet positions are the same (they depend on the
  instant, not the place). Relocation is a real, deliberate SR choice in modern practice.

## The bridge to natal
The four SR key points — SR Ascendant, MC, Sun, Moon — are mapped onto your natal chart: which natal
house each falls in, and their tight (≤2°) contacts to your natal planets/angles. This is where the SR
"lands" on your life ("SR Ascendant in your natal 10th, conjunct natal Saturn").

## Usage
```
natal-astrology/scripts/.venv/bin/python natal-astrology/scripts/solar_return.py \
  --name ABC --date 2000-01-01 --time 12:00 \
  --lat 51.5074 --lon -0.1278 --tz Europe/London --city London \
  --year 2026 \
  [--loc-lat 40.71 --loc-lon -74.01 --loc-tz America/New_York --loc-city "New York"]
```
`--year` defaults to the current year. Omit `--time` if the birth time is unknown (SR flagged). Without
`--out`, prints to stdout; with `--out`, writes markdown to that path.

## Output & privacy
Reveals the natal chart + a year's timing and location — personal. Default output (when saved):
`natal-astrology/solar-return-reports/` — **gitignored**.

## 中文 terms
太阳返照/生日盘 solar return · 返照盘 return chart · 异地返照 relocated SR · 本命宫位 natal house.
Reliable angles need a known birth time.
