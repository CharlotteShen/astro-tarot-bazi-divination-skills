# Tarot reading-quality evals — v2.0.1 (dev infra)

Deterministic checks for the tarot READING layer (draw mechanics have their own test suite). Same
harness as `natal-astrology/evals/` — a pinned **seed** makes each fixture's draw ground truth
forever. Catches: **fabrication** (citing cards not in the draw), **missed headlines** (not reading
a drawn card, or ignoring a reversal), **dropped flags** (seed not shown), and the reading-method's
**banned Barnum advice** ("trust your intuition", 顺其自然, …).

## Procedure
1. **Generate.** For each fixture in `fixtures/*.json`, produce a reading following `tarot/SKILL.md`
   exactly: run `python3 tarot/scripts/draw.py --spread <spread> --seed <seed> --question "<q>"`
   with the fixture's pinned values, then read per `references/reading-method.md` in the fixture's
   `language`. Save to `runs/<fixture>.md` (this folder is gitignored).
2. **Grade.** From the repo root:
   `natal-astrology/scripts/.venv/bin/python natal-astrology/scripts/eval_reading.py \
     --expect tarot/evals/fixtures/<f>.expect.json --reading tarot/evals/runs/<f>.md`
   (the grader is pure stdlib — any `python3` works). Exit 0 = all checks pass.
3. **Manual rubric** — what regexes can't judge. For each reading check:
   - [ ] Per-card-in-position: meaning = card × position × the actual question (no generic card lecture).
   - [ ] Whole-spread layer present: suit/element distribution, majors ratio, reversal density, interactions.
   - [ ] Synthesis is ONE narrative ending in a concrete step tied to a time or action.
   - [ ] Reversals read as inward/blocked/overdone — never plain "bad card".
   - [ ] Agency-first tone; crisis rule and hard boundaries per `voice-and-ethics.md`.
   - [ ] Language follows the fixture (EN / 中文 card names from `cards.md`).

## When to run
Before major releases and after any change to `tarot/references/reading-method.md` or `tarot/SKILL.md`.

## Verdicts are advisory
FAIL means "inspect", not "the reading is wrong" — a grounded paraphrase can defeat a pattern; widen
the pattern, never weaken the reading. Fabrication hits are almost always real bugs.

## Fixtures & regeneration
Fixture questions are generic (fake ABC profile) — safe to track. Expectation skeletons come from
`python3 tarot/scripts/make_expect.py --fixture fixtures/<f>.json` (re-draws the pinned seed, emits
JSON to stdout), then are hand-tuned and committed. `test_make_expect.py` asserts committed
expectations stay consistent with their pinned draws.
