# Birth-time sensitivity report — v1.1.5

On-request diagnostic for an uncertain birth time. Given a date + a time RANGE (not a single time), it
reports which chart factors are **stable** across the whole range vs. **sensitive** (they flip somewhere
inside it), with the exact flip minute pinpointed. This is NOT rectification — it does not use life
events to narrow the time down; it only shows how much precision matters. Full rectification is a
later, separate feature (out of scope here — see `SKILL.md` "Out of scope").

## Requirements
- **Route A only.** Needs a computed chart at several candidate times — cannot work from a Route-B
  single paste. If the user only has a Route-B chart, ask for date/lat/lon/tz/city to run this.

## How it works (plain terms)
1. The range is sampled every 15 minutes.
2. For each sample, ~44 chart factors are captured: the Ascendant and MC (sign), each of the 10
   planets' house, the Moon's sign, day/night sect, the three Arabic lots (sign + house), the Vertex
   (sign + house), the Sun/Moon midpoint (sign + house), and whether each planet is within 6° of the
   Ascendant or MC (an "on the angles" convention already used in readings).
3. Wherever two adjacent 15-minute samples disagree on a factor, the exact minute it flips is pinned
   down by bisection (repeatedly halving the interval) to within 1 minute.
4. Factors that never change across the whole range are reported **stable**; factors that do are
   reported **sensitive**, with an ordered timeline of when each value holds.

## Usage
```
natal-astrology/scripts/.venv/bin/python natal-astrology/scripts/sensitivity.py \
  --name ABC --date 2000-01-01 --time-start 06:00 --time-end 18:00 \
  --lat 51.5074 --lon -0.1278 --tz Europe/London --city London \
  --out natal-astrology/sensitivity-reports/abc.md
```
Without `--out`, the report prints to stdout instead of being saved.

## Output & privacy
A sensitivity report reveals real chart placements tied to a real (if uncertain) birth window — treat it
as personal data. Default output location: `natal-astrology/sensitivity-reports/` — **gitignored**.

## Conventions (own choices, tunable — constants in `scripts/sensitivity.py`)
- Coarse-scan step: **15 minutes** (`COARSE_STEP_MINUTES`) — safe because the fastest tracked factor
  (a planet entering/exiting the ±6° angle orb) takes about 48 minutes to fully cycle, so it can't hide
  inside one 15-minute window.
- Bisection tolerance: **1 minute** (`BISECT_TOLERANCE_MINUTES`).
- Angle orb: **6°** (`ANGLE_ORB`) — the same "planets on the angles" convention `reading-method.md`
  already uses, not a new number.
- Assumes Ascendant/MC move in one direction within any 15-minute window (true for non-polar
  latitudes); not validated at extreme polar latitudes.

## 中文 terms
出生时间范围 time range · 稳定 stable · 敏感/易变 sensitive · 翻转时刻 flip time · 校时 rectification
(a separate, later feature — this report does not do rectification)
