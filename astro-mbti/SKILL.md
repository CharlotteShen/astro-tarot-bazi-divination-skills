---
name: astro-mbti
description: "Playful folklore game: predicts your MBTI type from your natal chart via a deterministic weighted-heuristic script — explicitly NOT a measurement (astrology→MBTI has no scientific correlation, and the output says so). Per-axis leanings + driving chart factors + confidence first; the four-letter type is a just-for-fun rollup. English/中文. Triggers on: predict my MBTI with astrology, MBTI from my chart, what MBTI does my chart suggest, 星盘测 MBTI, 占星 MBTI, 我的星盘是什么 MBTI. Does NOT trigger on MBTI questions unrelated to astrology/natal charts. Requires the natal-astrology skill installed alongside (imports its chart engine) and Python."
---

# Astro-MBTI（民俗游戏 · folklore game）

You present the output of a deterministic scoring script. You do NOT compute or adjust
the type yourself — **never eyeball the table, never hand-compute weights**. If the
script cannot run (no Python / natal-astrology missing), say so honestly and stop;
there is no manual fallback.

## On every invocation
1. **Find the chart data** in this order: (a) `natal-astrology/birth-data.md` (the
   canonical location, shared with the natal skill); (b) the current working
   directory; (c) a path the user gives. If none exists, follow natal-astrology's
   "First-time setup" (its `SKILL.md`) to create one — never guess positions.
2. **Read `references/mbti-method.md`** — presentation order, canonical disclaimer,
   red lines, and the weight-table mirror all live there.
3. **Run the scorer** (stdout only; it never writes files):
   ```bash
   natal-astrology/scripts/.venv/bin/python astro-mbti/scripts/mbti_score.py \
     --birth-data natal-astrology/birth-data.md [--lang en|zh] [--json]
   ```
   (Substitute the `--birth-data` path you actually located in step 1.)
   No birth-data file? Pass explicit `--date YYYY-MM-DD --time HH:MM --lat .. --lon ..
   --tz ..`; unknown birth time → `--time-unknown` (degraded mode, see method doc).
4. **Present the reading** following mbti-method.md's mandated order: per-axis
   leanings with factors in plain language FIRST, then the type rollup with the
   canonical disclaimer, then the lineage footnote. Translate factor jargon into
   warm, plain second-person language (voice per natal `voice-and-ethics.md`), but
   never alter scores, letters, confidence, or the disclaimer wording. Pronouns come
   from the `gender` field of the birth-data file found in step 1 — never assumed
   from the name.
5. If the user wants to save the report, save under `astro-mbti/reports/`
   (gitignored — it contains birth data).

## Red lines（一票否决）
- The type must NEVER be reused as ground truth later in the conversation
  （禁「既然你是 INFJ…」— determinism through the back door）.
- No equivalence or diagnosis phrasing（禁「你就是」「测出」「你的真实类型是」）.
- The disclaimer block is mandatory, verbatim, and never moved before the axes.
- Never hand-compute or approximate the weight table — the script is the only
  scorer; a no-Python environment gets an honest refusal, not an estimate.
- Near-tie axes must show both candidates — never fake certainty.
- All natal voice-and-ethics red lines carry over (tendencies not certainties,
  no fatalism, agency, gender/pronouns from the `gender` field — never assumed).

## Language
Default = the `language` field of the birth-data file (`en` or `zh`); explicit switch
only ("switch to Chinese" / "用中文"), per repo convention. Meaning never changes with
language — only the wording.
