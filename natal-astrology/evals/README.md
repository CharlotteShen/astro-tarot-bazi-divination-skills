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

## 文风 rubric（v4.1.0）

机械门禁先跑：

```bash
python3 scripts/prose_scan.py natal-astrology/evals/runs
```

必须 PASS。然后人工/模型过六项：

1. 破折号为零（扫描器已机械确认，此处只复核 runs 之外的临场产出）。
2. 无格言公式、无制造金句（"X 是 Y 的 Z"、每段收在可截图的一句上）。
3. 句长有变化，不是通篇中等长度。
4. 三项并列处，确实有三项，不是为凑周全。
5. 收尾落在具体盘面事实上，不是一句祝福或上扬送别语。
6. 中文输出无四字格连排、无翻译腔。

**门禁强度如实说明：** 扫描器是硬门，但它只认识字符模式——破折号、超长粗体、内联
标题、少量词表。上面第 2、3、5、6 项它**判不了**，只能靠人看。rubric 不通过不等于
脚本会红。别把扫描器 PASS 当成文风合格。

判定依据：`natal-astrology/references/prose-style.md`。
