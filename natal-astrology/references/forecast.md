# Transit forecast timeline — v1.2.1

On-request forecast: over a date range (default the next 12 months), which transiting bodies perfect an
aspect to the natal chart, on exactly which date(s) — including retrograde multi-passes — and how long
each is roughly "in effect" (±1°). This is the "when does it go exact / what's coming up" companion to
the v1.2.0 snapshot ("what's active right now").

## Requirements
- **Route A only.** Needs the natal chart + a daily ephemeris scan across the range.

## Movers and targets
- **Movers (8):** Jupiter, Saturn, Uranus, Neptune, Pluto, Chiron, North Node (the slow, forecast-worthy
  ones) + Mars (the fastest transit still worth dating). The Sun/Moon/Mercury/Venus perfect too often to
  forecast — they're the snapshot's job.
- **Targets:** natal planets + Chiron + North Node, plus natal Ascendant/MC **when birth time is known**
  (omitted otherwise).

## How it works (plain terms)
1. The transiting positions are sampled once per day across the range.
2. For each mover/target/aspect, the signed distance from exact is tracked; each time it crosses zero, the
   aspect perfects — the exact date is interpolated on the daily grid. A planet that stations and backs
   over a point crosses zero 2–3 times, so retrograde multi-passes appear as multiple dated hits (tagged Rx).
3. The ±1° "in effect" window is read off the same daily data.

## Output
Two groups, chronological by first exact date: **Major transits** (Jupiter and slower — the long-lasting
ones) and **Mars triggers** (fast, days-long). Each line lists the exact date(s), retrograde marks, and
the in-effect window.

## Caveat on the in-effect window
The window is measured within the scanned range only. A very slow mover (e.g. Pluto, Neptune, or the
North Node) can stay within 1° of exact for longer than the whole range, in which case the reported
window clamps to your `--from`/`--to` bounds — the true in-effect span may extend beyond them. Widen the
range to see the full window.

## Usage
```
natal-astrology/scripts/.venv/bin/python natal-astrology/scripts/forecast.py \
  --name ABC --date 2000-01-01 --time 12:00 \
  --lat 51.5074 --lon -0.1278 --tz Europe/London --city London \
  --from 2026-07-01 --to 2027-07-01
```
`--from` defaults to today, `--to` to `--from` + 365 days. Omit `--time` if the birth time is unknown
(angles suppressed). Without `--out`, prints to stdout; with `--out`, writes markdown to that path.

## Output & privacy
Reveals the natal chart + dated life timing — personal. Default output (when saved):
`natal-astrology/forecast-reports/` — **gitignored**.

## Validation
The date-finding was checked against a publicly-documented event: reproducing Saturn's ingress into Aries
(enters 2025-05-25, retrogrades back to Pisces 2025-09-01, re-enters 2026-02-14) matched the published
dates to the day, retrograde step included. Positions match NASA JPL Horizons to arcseconds (see the
v1.2.0 `references/transits.md` validation note).

## 中文 terms
流年/未来行运 forecast · 精确日期 exact date · 逆行 retrograde · 生效期 in-effect window. Timing to the
day; not a promise of events.
