# Birth-data setup

Five of the six skills read a chart. Rather than ask you for your birth details every
time, they read them **once** from a single private file. This page shows you how to
create that file — no coding background assumed.

Throughout, the worked example is a made-up person, **ABC**, born **1 January 2000 at
12:00 in London**. Wherever you see ABC's values, put your own in their place.

- [What `birth-data.md` is](#what-birth-datamd-is)
- [Route B — no Python (paste from astro.com)](#route-b--no-python-paste-from-astrocom)
- [Route A — with Python (one command)](#route-a--with-python-one-command)
- [For 八字 / 紫微 / 宿曜](#for-八字--紫微--宿曜)
- [A second person (relationship readings)](#a-second-person-relationship-readings)
- [Privacy: what stays on your machine](#privacy-what-stays-on-your-machine)

---

## What `birth-data.md` is

It is one plain-text file that lives at:

```
natal-astrology/birth-data.md
```

That single file powers **all** the chart-based skills — Western astrology, 八字, 紫微斗数,
宿曜, and the 中西合参 synthesis. You fill it in once.

- It does **not** exist yet when you clone the repo — you create it from a template.
- The template is [`natal-astrology/birth-data.template.md`](../natal-astrology/birth-data.template.md).
- The finished `birth-data.md` is **gitignored**: it never gets committed, never leaves your
  computer. (See [Privacy](#privacy-what-stays-on-your-machine) below.)

To start, copy the template to its real name:

```bash
cp natal-astrology/birth-data.template.md natal-astrology/birth-data.md
```

(The `install.sh` script offers to do this copy for you.) Then fill it in using **one** of
the two routes below. You do not need both.

| | Route B | Route A |
|---|---|---|
| **Needs Python?** | No | Yes |
| **Where the numbers come from** | You paste them from [astro.com](https://www.astro.com) | A script computes them |
| **Best if** | You just want to read your chart with zero setup | You also want chart wheels, transits, forecasts, and the other predictive tools |

---

## Route B — no Python (paste from astro.com)

This works anywhere and needs no installation. You get an accurate chart from a free
website and copy the numbers into the template.

1. Go to [astro.com](https://www.astro.com) → **Free Horoscopes** → **Extended Chart
   Selection**.
2. Enter the birth date, exact time, and birthplace. Chart type: **Natal Chart Wheel**.
   House system: **Placidus** (the default).
3. Click **"Additional tables (PDF)"** above the chart. That PDF lists, as text, the
   **positions table** (each planet's sign, degree, house, and an `R` if retrograde), the
   **ASC / MC**, and the **aspect grid**.
   - Easier to copy: [astro-seek.com](https://www.astro-seek.com) shows the same data in
     plain HTML tables that select-and-copy cleanly.
   - No-typing shortcut: you can also just hand the PDF to Claude and ask it to fill the
     template for you.
4. Copy those numbers into your `birth-data.md`. Keep every field name exactly as printed.

Filling the **Meta** block for ABC looks like this:

```
- name: ABC
- date: 2000-01-01
- time: 12:00
- location: London, United Kingdom
- lat: 51.51           # North is +, South is − (no N/S letter)
- lon: -0.13           # East is +, West is − (London is just west of 0°)
- tz: Europe/London
- house_system: Placidus
- zodiac: tropical
- source: astro.com
- language: en          # en or zh — your default reply language
- gender: she/her       # used only for correct pronouns
```

Then fill the **Planets**, **Angles**, **Points**, and **Aspects** blocks from the astro.com
tables. For the exact meaning of each field and the validation rules, see
[`natal-astrology/references/data-contract.md`](../natal-astrology/references/data-contract.md)
→ **"Route B — how to fill the file from astro.com"**. For a complete, already-filled file to
copy the shape from, see the fixture
[`natal-astrology/fixtures/sample_chart.md`](../natal-astrology/fixtures/sample_chart.md)
(a fictional sample person — not a real chart).

If you are missing a few aspects or the balance block, that is fine — the reading simply
won't comment on what isn't listed. The skill will tell you if something *required* is
missing; it will never invent a position to fill a gap.

---

## Route A — with Python (one command)

If you have Python 3, a script computes the whole chart for you (via the Swiss Ephemeris /
[kerykeion](https://github.com/g-battaglia/kerykeion)). This is also what unlocks the
predictive tools (transits, forecast, solar return, progressions…) and the chart-wheel
images — those all need Route A.

**1. Install the astrology engine:**

```bash
pip install -r natal-astrology/scripts/requirements.txt
```

**2. Generate the file** (ABC's values shown — swap in yours):

```bash
python natal-astrology/scripts/chart.py \
  --date 2000-01-01 --time 12:00 \
  --lat 51.51 --lon -0.13 --tz Europe/London --city London \
  --out natal-astrology/birth-data.md
```

That writes a complete, validated `birth-data.md`. Done.

### If `pip install` fails with "externally-managed-environment"

On newer macOS (Homebrew) and Debian/Ubuntu Python, installing packages system-wide is
blocked (this is [PEP 668](https://peps.python.org/pep-0668/)). It is not an error you did
anything wrong — just use a **virtual environment** (a private, self-contained Python folder):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r natal-astrology/scripts/requirements.txt
```

Then **start Claude Code from that same terminal window** (the one where you ran
`source .venv/bin/activate`), so Claude's scripts can see the installed packages. This
matches the guidance `install.sh` prints. If you would rather not deal with Python at all,
Route B above needs none of this.

---

## For 八字 / 紫微 / 宿曜

The Chinese systems read the **same** `natal-astrology/birth-data.md` — you don't keep a
separate file. Two small things to add:

- **Fill `bazi_gender`** — `男` or `女`. 八字 and 紫微 use it to decide the direction of the
  大运 / 大限 (luck cycles). It is separate from the `gender` pronoun field. For ABC:
  `bazi_gender: 女`.
- **Install the engines** (Route A only — 八字 and 紫微 have no paste route):

  ```bash
  pip install -r bazi/scripts/requirements.txt -r ziwei/scripts/requirements.txt
  ```

  This installs `lunar-python` (used by both 八字 **and** 宿曜) and `iztro-py` (used by
  紫微). 宿曜 needs no separate install beyond this.

What each system needs from your birth data:

| System | Needs an exact birth **hour**? | Notes |
|---|---|---|
| **八字** BaZi | Preferred, not required | If the hour is unknown it casts a **three-pillar** chart and says so. |
| **紫微** Zi Wei | **Yes, required** | No unknown-hour fallback. Without an hour, use 八字 instead. |
| **宿曜** Xiuyao | **No** — birth **date only** | The time of day is irrelevant; only the calendar date matters. |

---

## A second person (relationship readings)

For any two-person reading — Western synastry, 合八字, 宿曜三九相性, or the 中西合参
synthesis — add the other person as a **second file**, same template, same folder:

```
natal-astrology/birth-data-2.md
```

Create it exactly like the first (Route A or Route B), giving the second person's details.
It is gitignored too. Once both files exist, you can ask things like *"compare my chart with
theirs"*, *「合个八字」*, or *「中西合参」*. See the
[skills guide](skills-guide.md) for what each two-person reading offers.

---

## Privacy: what stays on your machine

Your birth data is personal, so the repo's [`.gitignore`](../.gitignore) is built to keep it
from ever being committed or pushed. What each pattern protects:

| Pattern | Protects |
|---|---|
| `birth-data.md`, `birth-data-*.md`, `**/birth-data*.md` | Your chart file and the second-person file, anywhere in the repo. |
| `*-birth-data.md`, `Birth Data *.md` | Alternately-named chart files (e.g. exports). |
| `natal-astrology/charts/` | Chart-wheel images (a wheel reveals the whole birth chart). |
| `*/reports/`, `natal-astrology/*-reports/` | Saved readings for every skill (they contain your chart and your question). |
| `*/evals/runs/` | Locally generated eval readings. |
| `tarot/readings/` | Saved tarot readings (they contain your question). |
| `synastry.md`, `relationship.json` | Two-person relationship outputs (they hold **both** people's birth data). |

The rule of thumb: **anything personalised stays local.** The skills only ever read these
files; they never send them anywhere. If you ever open a GitHub issue, use the fictional
profiles (ABC and friends), never your real birth details.

**Keep your details in the shapes the guardrails recognise.** The protection above keys off two
things: (1) the **filenames** in the table, and (2) the template's **`- field:` lines** where
your birth details live. So:

- Put your data in `birth-data.md` / `birth-data-2.md` using the template's fields — don't rename
  those files or invent a differently-named data file for personal details.
- Let generated readings save into the `reports/`, `charts/`, `readings/` folders (the skills do
  this by default); don't move them elsewhere in the repo.
- Before you commit anything (only relevant if you fork and push), run `git status` — your birth
  data and readings should never show up as tracked. If one does, it's in the wrong place; move it
  back into a gitignored file or folder above.

---

*Next: the [skills guide](skills-guide.md) — what each of the six skills does and how to ask
for it. Back to the [README](../README.md).*
