# For developers

This page is for people who want to run the tests, understand the reading-quality evals,
know which numbers are tunable conventions, or contribute. If you only want to *use* the
skills, you don't need any of this — see [birth-data setup](chart-setup.md) and the
[skills guide](skills-guide.md).

- [How this repo relates to the private one](#how-this-repo-relates-to-the-private-one)
- [Running the tests](#running-the-tests)
- [Reading-quality evals](#reading-quality-evals)
- [Conventions (so you know what's a choice)](#conventions-so-you-know-whats-a-choice)
- [Contributing](#contributing)

---

## How this repo relates to the private one

This public repo is a **curated mirror**. The skills are developed in a separate private
repository (with real-data end-to-end testing that can't be public), and the skill folders
are **synced out** to here after review. Practically, that means:

- **Changes to skill folders are made upstream**, in the private repo, then published here.
  A pull request that edits skill logic is very welcome as a *proposal*, but the change lands
  by being re-applied upstream and re-synced — not merged directly — so don't be surprised if
  a maintainer reworks it rather than clicking merge.
- **Issues and PRs are welcome** — bug reports, doc fixes, new fixtures, reference-file
  clarifications, all good.
- **Never put real birth data in an issue or PR.** Use the fictional profiles only (ABC,
  XYZ, UNK — see below). A real birth date + time + place *is* personal data.

---

## Running the tests

Each skill's `scripts/` folder has a `pytest` suite (calculation correctness — the layer that
must be exact). Install the engines first, then run all six suites from the repo root:

```bash
# one-time: install the calculation engines
pip install \
  -r natal-astrology/scripts/requirements.txt \
  -r bazi/scripts/requirements.txt \
  -r ziwei/scripts/requirements.txt

# run every skill's tests
python3 -m pytest \
  natal-astrology/scripts tarot/scripts bazi/scripts \
  ziwei/scripts xiuyao/scripts hecan/scripts
```

Notes:

- If `pip install` reports `externally-managed-environment`, use a virtual environment — see
  [birth-data setup → Route A](chart-setup.md#if-pip-install-fails-with-externally-managed-environment),
  then run `pytest` from that same activated shell.
- `tarot/scripts` uses only the standard library, and 宿曜's engine (`lunar-python`) comes in
  with the 八字 requirements — so the three installs above cover all six suites.
- These tests check the **calculation**, not the readings. Reading quality is checked
  separately, by the evals below.

---

## Reading-quality evals

Every skill has an `evals/` folder that checks the **interpretation** layer — the part a plain
unit test can't see. Each holds fixture charts plus expectation files, and a grader script
grades a generated reading against them. The checks catch:

- **fabrication** — citing a factor that isn't in the chart;
- **missed headlines** — ignoring the tightest verified factors;
- **dropped reliability flags** — e.g. omitting the unknown-birth-time caveat.

The procedure (see each `evals/README.md`): for every fixture, generate a reading by following
that skill's `SKILL.md` exactly and save it to `evals/runs/<fixture>.md`; then run the skill's
`eval_reading.py` (or the per-skill equivalent) against the fixture's `.expect.json`. Exit 0
means all checks passed; a per-item table shows what hit or missed. There's also a manual
rubric for the qualitative things regexes can't judge (genuine synthesis, two-sidedness, no
Barnum statements, empowering tone, correct language and pronouns).

Two things to keep in mind:

- **Verdicts are advisory.** A `FAIL` means *"inspect,"* not *"the reading is wrong"* — a
  grounded paraphrase can trip a pattern. If a reading is genuinely grounded, widen the
  pattern rather than weakening the reading. (Fabrication hits are the exception — those are
  almost always real bugs.)
- **Fixtures are fake profiles** (ABC London, XYZ Paris, UNK Sydney) and are safe to track;
  the pinned seeds and pinned `--date` values make expectations deterministic forever. The
  `evals/runs/` output folders are **gitignored** (a generated reading is personal even when
  the fixture isn't).

The six `evals/README.md` files —
[natal](../natal-astrology/evals/README.md) ·
[tarot](../tarot/evals/README.md) ·
[bazi](../bazi/evals/README.md) ·
[ziwei](../ziwei/evals/README.md) ·
[xiuyao](../xiuyao/evals/README.md) ·
[hecan](../hecan/evals/README.md) —
have the exact commands per skill. This is dev tooling, not a reading feature.

---

## Conventions (so you know what's a choice)

Most of the methods follow standard or verified references. A handful of settings are our own
tunable choices, not a single authority — listed here verbatim so nothing is a black box.
Every one is a named constant in a script and easy to change; none is "wrong."

> The methods/formulas follow standard or verified references (tropical zodiac, Placidus default, 5 major
> aspects, composite = longitude midpoints, Davison = time-space midpoint, Hellenistic lots, Swiss-Ephemeris
> declination/Vertex). A few settings are **our own tunable choices**, not a single authority:
> - **Aspect orbs**: 8° (conjunction/opposition/square/trine), 6° (sextile).
> - **Composite houses**: whole-sign from the composite Ascendant (a simplification of a debated topic).
> - **Davison location**: simple mean of the two latitudes/longitudes (off near the antimeridian).
> - **Focal point**: a planet in ≥2 cross-aspects (the "hotspot" threshold).
> - **Enrichment orbs**: midpoint ≤1.5°, declination parallel ≤1°, asteroid/Lilith contact ≤2° (constants
>   in `scripts/chart.py`).
> - **Sensitivity scan**: 15-minute coarse step, 1-minute bisection tolerance, ±6° angle orb (constants
>   in `scripts/sensitivity.py`).
> - **Rectification**: 5-major aspects, full-chart-recompute progressed angles, 365.25-day year, top-8
>   ranked candidates (constants in `scripts/rectification.py`).
> - **Transits**: tighter orbs (3° majors, 2° sextile, +2° for the Moon), noon positions, slow/fast
>   grouping (constants in `scripts/transits.py`).
> - **Transit forecast**: slow movers + Mars, daily scan with day-resolution exact dates, ±1° in-effect
>   window, default 12-month range (constants in `scripts/forecast.py`).
> - **Solar Return**: return moment found birthday ±2 days (minute precision), bridge = SR ASC/MC/Sun/Moon
>   to natal houses + 2° contacts, birth-location default (constants in `scripts/solar_return.py`).
> - **Profections**: traditional 7-classical rulerships, whole-sign houses from the rising sign, monthly =
>   1/12-year segments (constants in `scripts/profections.py`).
> - **Progressions**: day-for-a-year (365.25), full-recompute angles, 1° contact orb, 8×45° lunation
>   phases, noon reference date (constants in `scripts/progressions.py`).
> - **Solar arc**: exact progressed-Sun arc (not 1°/yr approximation), five majors at 1°, timing from the
>   actual arc rate, self-pairs excluded (constants in `scripts/solar_arc.py`).
>
> All are easy to adjust; none are "wrong" — just conventions.

(Script paths above are relative to the `natal-astrology/` skill folder — e.g.
`scripts/chart.py` is [`natal-astrology/scripts/chart.py`](../natal-astrology/scripts/chart.py).)
The Chinese systems carry their own convention notes in their reference files —
[`bazi/references/conventions.md`](../bazi/references/conventions.md),
[`ziwei/references/conventions.md`](../ziwei/references/conventions.md), and each skill's
`references/method.md`.

---

## Contributing

- **Fake profiles only.** Any fixture, issue, or PR must use the fictional profiles (ABC,
  XYZ, UNK) — never a real birth date + time + place. The `.gitignore` blocks the personal
  files by default; keep it that way.
- **Keep added filenames ASCII.** This public tree is produced from a private dev repo by a
  sync script whose safety firewall verifies each file against `git ls-files` by literal path.
  Git C-quotes non-ASCII paths (`"\346..."`), so a tracked file with a non-ASCII name would fail
  that check and block a sync. ASCII filenames (English content inside is fine) avoid it.
- **Language.** Four of the six skills (八字, 紫微, 宿曜, 中西合参) read and reply **中文为主** —
  their reference files and much of their reading logic are in Chinese. Contributions to those
  skills should keep that voice; natal astrology and tarot are English-first with a 中文 switch.
- **Where to start.** Doc fixes and new deterministic fixtures are the easiest first
  contributions. For skill-logic changes, open an issue describing the behaviour first — since
  changes land upstream and sync back (see [above](#how-this-repo-relates-to-the-private-one)),
  a discussion up front saves rework.

---

*Back to the [skills guide](skills-guide.md) or the [README](../README.md).*
