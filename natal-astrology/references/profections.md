# Profections — v1.3.1

The Hellenistic "time-lord" technique. Each year of life activates a whole-sign house rotating from the
Ascendant, and the ruler of that house's sign becomes the **lord of the year** — the planet whose natal
condition and transits set the year's theme. The monthly sub-cycle does the same at ~1/12-year steps.

## The technique
- **Annual:** profected house = `(age mod 12) + 1`, counting the rising sign as the 1st at age 0. The
  profected sign is that whole sign from the rising sign; its traditional ruler is the lord of the year.
  Where that lord sits natally (sign/house), and any natal planets in the profected sign, are activated.
- **Monthly:** from the birthday, each ~1/12 of the year (~30.4 days) advances one house from the annual
  house, cycling all twelve within the year.

## Rulerships (traditional / 7 classical)
Aries/Scorpio→Mars, Taurus/Libra→Venus, Gemini/Virgo→Mercury, Cancer→Moon, Leo→Sun,
Sagittarius/Pisces→Jupiter, Capricorn/Aquarius→Saturn. Profections are a Hellenistic technique, so the
lord of the year is always one of the seven visible planets — modern outer-planet rulers are not used.

## Reliability
The profected **house number** comes from your age alone (always reliable). The profected **sign, lord,
lord placement, and activations** all depend on the **rising sign**, which needs a known birth time —
without it, only the house number is trustworthy (the report flags this).

## Usage
```
natal-astrology/scripts/.venv/bin/python natal-astrology/scripts/profections.py \
  --name ABC --date 2000-01-01 --time 12:00 \
  --lat 51.5074 --lon -0.1278 --tz Europe/London --city London \
  --on 2026-07-02
```
`--on` (reference date) defaults to today. Omit `--time` if the birth time is unknown (flagged). Without
`--out`, prints to stdout; with `--out`, writes markdown to that path.

## Output & privacy
Reveals the natal rising sign + placements — personal. Default output (when saved):
`natal-astrology/profection-reports/` — **gitignored**.

## 中文 terms
小限法 annual profection · 年主星 lord of the year · 月主星 monthly lord · 本命上升 rising sign.
Traditional rulerships; reliable sign/lord needs a known birth time.
