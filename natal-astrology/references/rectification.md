# Lightweight rectification — v1.1.6

On-request aid for narrowing an uncertain birth time using known life events. Given a time RANGE +
one or more dated events, it scores each candidate time by how well two classical techniques line up
with those events, and reports a **ranked** list — never a declared "true" time. This is heuristic
corroboration, not proof, and it is **not** solar arc directions (a third technique, deferred).

## Requirements
- **Route A only.** Needs computed charts at many candidate times — cannot work from a Route-B paste.
- At least one event: a date + a free-text description ("started my current job", "moved abroad").

## The two techniques (both reuse chart.py's aspect engine)
- **Progressed angles/Moon** — secondary progression ("day-for-a-year"): for an event at age N years,
  the progressed chart is the natal chart recomputed for N days after birth (keeping the candidate's
  own time/place). Its Ascendant, MC, and Moon are checked for an aspect to the natal planets/angles.
- **Transits to the angles** — the real planet positions on the event date, checked for an aspect to
  the candidate's natal Ascendant/MC only (natal planet positions barely move across same-day
  candidates, so only the angles carry rectification signal).

Each near-aspect (our 5 majors, standard orbs) is one "hit"; a candidate's score is its total hits
across all events. Higher score = better corroborated. Transit positions are computed once per event
(they don't depend on the birth-time guess); progressed charts are per candidate.

## Usage
```
natal-astrology/scripts/.venv/bin/python natal-astrology/scripts/rectification.py \
  --name ABC --date 2000-01-01 --time-start 06:00 --time-end 18:00 \
  --lat 51.5074 --lon -0.1278 --tz Europe/London --city London \
  --event 2020-03-15:started my current job \
  --event 2022-08-01:moved abroad \
  --out natal-astrology/rectification-reports/abc.md
```
Without `--out`, the report prints to stdout. `--event` is repeatable; at least one is required.

## Output & privacy
The report reveals real chart placements AND the user's event dates/labels — treat all of it as
personal. Default output location: `natal-astrology/rectification-reports/` — **gitignored**. Events
are ephemeral: passed fresh each run, never written into `birth-data.md` or any tracked file.

## Conventions (own choices, tunable — constants in `scripts/rectification.py`)
- Aspect set/orbs: the project's 5 majors (conj/opp/sq/tri 8°, sextile 6°), not "hard aspects only".
- Progressed-angle method: full chart recompute at the progressed moment (not solar-arc-on-MC).
- Secondary-progression year length: 365.25 days.
- Transit reference time: noon local on the event date (event's exact time is usually unknown).
- Candidate step: 15 minutes (reused from `sensitivity.py`). Displayed depth: top 8 (`TOP_N_DISPLAYED`).

## 中文 terms
校时/生辰校正 rectification · 二次推运 secondary progression · 行运 transit · 推运上升/中天 progressed
ASC/MC · 事件 event. This is a heuristic aid, not a guaranteed birth time.
