# Reading-quality evals — v1.3.2 (dev infra)

Deterministic checks for the READING layer (calculation already has its own test suite). Catches:
**fabrication** (citing factors not in the chart), **missed headlines** (ignoring the tightest verified
factors), **dropped reliability flags** (e.g. no unknown-birth-time caveat).

## Procedure
1. **Generate.** For each fixture in `fixtures/*.json`, produce a reading following `SKILL.md` exactly
   (natal synthesis / synastry reading / transit relay; the fixture's `reading_type` says which). Save to
   `runs/<fixture>.md` (this folder is gitignored).
2. **Grade.** From the repo root:
   `natal-astrology/scripts/.venv/bin/python natal-astrology/scripts/eval_reading.py \
     --expect natal-astrology/evals/fixtures/<f>.expect.json --reading natal-astrology/evals/runs/<f>.md`
   Exit 0 = all checks pass; the per-item table shows what hit/missed.
3. **Manual rubric** — what regexes can't judge. For each reading check:
   - [ ] Synthesis: every claim weaves ≥2 chart factors (no cookbook listicle).
   - [ ] Two-sided: gifts AND frictions named; contradictions adjudicated, not averaged.
   - [ ] No Barnum statements ("you can be both X and Y").
   - [ ] Empowering, non-fatalistic; no medical/legal/financial/death claims.
   - [ ] ~70% plain language / 30% technical; meaning leads, data supports.
   - [ ] Correct language (en/zh per the birth file) and stated pronouns.

## When to run
Before major releases (e.g. the v2.0.0 pivot) and after any change to `reading-method.md` or `SKILL.md`.

## Verdicts are advisory
A FAIL means "inspect", not "the reading is wrong": a grounded paraphrase can defeat a pattern. If the
reading is genuinely grounded, widen the pattern (add a variant) — never weaken the reading to fit the
regex. Fabrication (forbidden) hits, by contrast, are almost always real bugs in the reading.

## Fixtures
All fake profiles (ABC London, XYZ Paris, UNK Sydney) — safe to track. The transit fixture pins
2026-07-01 so its expectations stay deterministic forever. Expectation values were authored from
verified script output (see the v1.3.2 design spec).
