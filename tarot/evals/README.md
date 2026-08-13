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

## 文风 rubric（v4.1.0）

机械门禁先跑：

```bash
python3 scripts/prose_scan.py tarot/evals/runs
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

判定依据：`tarot/references/prose-style.md`。
