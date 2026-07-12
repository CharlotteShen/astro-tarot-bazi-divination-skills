# Secondary progressions — v1.3.3

The "day-for-a-year" inner clock: the chart's positions N days after birth describe year N of life.
Where transits are the outer weather and the Solar Return is the year's chart, progressions track slow
**inner development** — read via the progressed personal points, the progressed lunation phase, and
tight progressed-to-natal contacts.

## The technique
- **Day-for-a-year, full recompute** (365.25-day year; the same sourced convention as
  `references/rectification.md`): the progressed chart is a real chart cast for
  `birth_datetime + age_years days`, at the birth place.
- **Points read (7):** progressed Sun, Moon, Mercury, Venus, Mars, Ascendant, MC — each by sign/degree
  and by which **natal** house it now occupies. Outer planets are excluded (they barely move).
- **Progressed lunation phase:** the angle from prog Sun to prog Moon divides the ~30-year prog
  Sun–Moon cycle into 8 phases (New → Crescent → First Quarter → Gibbous → Full → Disseminating →
  Last Quarter → Balsamic) — a widely used life-chapter marker.
- **Contacts:** progressed points vs natal planets + ASC/MC, five majors at a **1° orb** (progressed
  motion is slow, so 1° means "active now": prog Moon ~1°/month, prog Sun ~1°/year).

## Reliability
A known birth time matters twice: progressed ASC/MC and all natal-house placements need it, and the
prog Moon inherits the natal Moon's time-sensitivity (±12h ≈ ±6.5°), which also blurs the lunation
phase. Without a birth time, only the prog Sun/Mercury/Venus/Mars signs are trustworthy (flagged).

## Usage
```
natal-astrology/scripts/.venv/bin/python natal-astrology/scripts/progressions.py \
  --name ABC --date 2000-01-01 --time 12:00 \
  --lat 51.5074 --lon -0.1278 --tz Europe/London --city London \
  --on 2026-07-02
```
`--on` defaults to today. Omit `--time` if the birth time is unknown (flagged). Without `--out`, prints
to stdout; with `--out`, writes markdown to that path.

## Output & privacy
Reveals the natal chart + inner timing — personal. Default output (when saved):
`natal-astrology/progression-reports/` — **gitignored**.

## 中文 terms
二次推运 secondary progressions · 推运月亮 progressed Moon · 推运月相 progressed lunation phase ·
推运上升/中天 progressed ASC/MC. Inner development, not event prediction.
