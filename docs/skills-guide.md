# Skills guide

Six divination skills live in this repo. Each is a folder Claude Code loads on its own once
[installed](../README.md#quickstart) — you never call a skill by name; you just say what you
want in plain language (English or 中文) and the matching skill wakes up.

A note that runs through all six: **the numbers are always computed by a script, never
guessed by the model.** Planetary positions, 排盘, 安星, tarot draws, 宿的排布 — all come from
deterministic engines. The skills' job is *interpretation*. That is why the readings are
grounded and reproducible.

Most skills need your chart set up first — see [birth-data setup](chart-setup.md). Tarot
is the exception: it needs nothing.

- [Natal astrology (Western)](#natal-astrology-western)
- [Tarot](#tarot)
- [八字 BaZi](#八字-bazi)
- [紫微斗数 Zi Wei Dou Shu](#紫微斗数-zi-wei-dou-shu)
- [宿曜 Xiuyao](#宿曜-xiuyao)
- [中西合参 East–West synthesis](#中西合参-eastwest-synthesis)

---

## Natal astrology (Western)

**What it is.** Modern-psychological Western astrology read from your accurate birth chart.
It does *whole-chart synthesis* (your chart told as one coherent story, not a list of
placements) and *per-planet drill-down* ("what does my Mars mean for my career?"). It also
covers a full predictive suite and two-person relationship charts (below). English or 中文.

**What to say.**

- English: *"read my chart"* · *"what's my chart about"* · *"tell me about my Venus"* ·
  *"what does my Saturn mean for money"* · *"what are my transits"* · *"what's coming up this
  year"* · *"my solar return"* · *"my progressions"* · *"show my chart wheel"* · *"compare my
  chart with theirs"*
- 中文：*本命盘* · *星盘解读* · *读读我的星盘* · *我的月亮是什么意思* · *行运* · *流年* ·
  *太阳返照* · *二次推运* · *画个星盘* · *合盘*

**What you get.** A synthesised reading that weaves at least two chart factors per point,
names both gifts and frictions, and stays empowering rather than fatalistic — no cookbook
listicles, no doom. The predictive and relationship tools each produce their own focused
report (a dated transit timeline, a year-ahead solar-return read, a synastry dynamic, and so
on).

**The bigger toolset.** Beyond the core reading, natal covers:

- **Predictive suite** — transits (what's active now), transit forecast (dated timeline of
  what's coming), solar return (year-ahead birthday chart), profections (lord of the year),
  secondary progressions (your evolving inner chart), and solar arc directions. See the
  reference files [`transits.md`](../natal-astrology/references/transits.md),
  [`forecast.md`](../natal-astrology/references/forecast.md),
  [`solar-return.md`](../natal-astrology/references/solar-return.md),
  [`profections.md`](../natal-astrology/references/profections.md),
  [`progressions.md`](../natal-astrology/references/progressions.md), and
  [`solar-arc.md`](../natal-astrology/references/solar-arc.md).
- **Synastry & relationship charts** — compare two charts (romantic / friendship / family /
  work), plus composite, Davison, and Marks charts. See
  [`synastry-method.md`](../natal-astrology/references/synastry-method.md) and
  [`davison-marks.md`](../natal-astrology/references/davison-marks.md).
- **Chart wheels** — an SVG image of any of the above; see
  [`wheels.md`](../natal-astrology/references/wheels.md).
- **Uncertain birth time** — a sensitivity scan and a light rectification aid; see
  [`sensitivity.md`](../natal-astrology/references/sensitivity.md) and
  [`rectification.md`](../natal-astrology/references/rectification.md).

**Example.** [English](examples/natal-astrology-en.md) · [中文](examples/natal-astrology-zh.md)

**Requirements.** The core reading works with **Route A or Route B**. The predictive suite,
chart wheels, and the sensitivity/rectification tools require **Route A** (they compute new
positions). A known birth time makes angle- and Moon-dependent results reliable; without it
the skill still reads, and flags what's uncertain. Setup: [birth-data setup](chart-setup.md).

---

## Tarot

**What it is.** Tarot readings from a full 78-card Rider–Waite deck, with seven spreads
(single, three-card, relationship, decision, horseshoe, monthly cycle, and Celtic Cross),
upright and reversed, in English or 中文. The cards are drawn **only** by
[`tarot/scripts/draw.py`](../tarot/scripts/draw.py) — a seeded, reproducible draw — so the
model never picks favourable cards.

**What to say.**

- English: *"draw me a tarot card"* · *"do a three-card spread on my job"* · *"tarot reading
  about this decision"* · *"pull a Celtic Cross"* · *"daily card"*
- 中文：*塔罗* · *抽一张牌* · *三张牌看看这段关系* · *帮我起个牌阵* · *凯尔特十字* · *每日一牌*

**What you get.** The spread's positions, the drawn cards and their orientations, and the
random seed (so a reading is reproducible). Then a reading that goes card-in-position →
whole-spread → one narrative, ending in a concrete, time- or action-specific step (never a
vague "the cards say be positive"). If your `birth-data.md` exists, it can optionally add an
astrology-resonance note — offered once, never required.

**Example.** [English](examples/tarot-en.md) · [中文](examples/tarot-zh.md)

**Requirements.** **None.** Tarot needs no birth data and no Python packages (`draw.py` uses
only the standard library). It works the moment the skill is installed.

---

## 八字 BaZi

**What it is.** 八字（四柱）命理解读，中文为主。排盘只用
[`bazi/scripts/bazi_chart.py`](../bazi/scripts/bazi_chart.py)（lunar-python 引擎，真太阳时校正，
模型永不自排干支）。固定分析顺序：排盘 → 身强弱 → 喜用神 → 大运 → 流年 → 流月。也支持双人
**合八字**。

**What to say.**

- 中文：*八字* · *批八字* · *排个盘看看* · *四柱* · *我的大运* · *今年流年怎么样* ·
  *身强身弱* · *喜用神* · *合八字* · *我们俩的八字合不合*
- English: *"read my BaZi / four pillars"* · *"what's my day master"* · *"my luck cycle this
  year"* — English questions get English answers.

**What you get.** 四柱排盘（年/月/日/时干支、十神、藏干、纳音、日主与月令），接着按固定顺序的
分层解读，结论 / 依据 / 建议分离，每个结论指回脚本输出的具体干支或十神。反宿命论、反巴纳姆，
建议具体到时间与动作，不打分、不判吉凶。**合八字** 读双方干支互动 + 喜用神互补 + 大运同频，
给相处功课而非兼容分数（见
[`bazi/references/match-method.md`](../bazi/references/match-method.md)）。

**Example.** [English](examples/bazi-en.md) · [中文](examples/bazi-zh.md)

**Requirements.** **Route A only** — 八字 has no paste route. Install the engine with
`pip install -r bazi/scripts/requirements.txt` and fill `bazi_gender`（男/女）in your
birth-data file. An exact birth **hour** is preferred; without it, 八字 casts a **three-pillar**
chart and states the precision impact. Setup: [birth-data setup](chart-setup.md).

---

## 紫微斗数 Zi Wei Dou Shu

**What it is.** 紫微斗数命盘解读，中文为主。安星只用
[`ziwei/scripts/ziwei_chart.py`](../ziwei/scripts/ziwei_chart.py)（iztro-py 引擎，模型永不自安星）。
三合派为主 + 四化层。固定分析顺序：命宫身宫 → 三方四正 → 生年四化 → 大限 → 流年 → 流月。

**What to say.**

- 中文：*紫微斗数* · *紫微* · *斗数* · *排个紫微盘* · *我的命宫* · *身宫* · *大限* · *四化* ·
  *我的化忌在哪* · *今年流年*
- English: *"read my Zi Wei Dou Shu / purple star chart"* — English questions get English
  answers.

**What you get.** 十二宫的命盘（14 主星 + 亮度、生年四化、大限 / 流年 / 流月三层），逐宫解读永不
孤宫（必看三方四正），结论 / 依据 / 建议分离，每个结论指回具体星曜 / 宫位 / 亮度 / 四化。
化忌、煞星、陷地一律按「功课」表述，禁灾祸恐吓，反宿命论。

**Example.** [English](examples/ziwei-en.md) · [中文](examples/ziwei-zh.md)

**Requirements.** **Route A only.** Install the engine with
`pip install -r ziwei/scripts/requirements.txt`. 紫微 **requires an exact birth hour** — there
is no unknown-hour fallback. If you don't know your hour, use 八字 instead (or narrow the hour
first with the natal sensitivity/rectification tools). Setup: [birth-data setup](chart-setup.md).

---

## 宿曜 Xiuyao

**What it is.** 宿曜占星（二十七宿）：本命宿性格、双人**三九相性**、值日宿日运。排宿只用
[`xiuyao/scripts/xiuyao_chart.py`](../xiuyao/scripts/xiuyao_chart.py)（lunar-python 引擎，模型永
不数宿）。中文为主。最大特点：**只需出生日期，不需时辰**。

**What to say.**

- 中文：*宿曜* · *星宿* · *我的本命宿* · *二十七宿* · *宿曜相性* · *我们的宿合不合* ·
  *今天的值日宿*
- English: *"what's my xiuyao / birth mansion"* · *"our xiuyao compatibility"* — English
  questions get English answers.

**What you get.** 本命宿的性格材料（光影成对呈现），双人时给**三九相性**——它的招牌特色是
**双向并陈**：同一段关系里「甲看乙」与「乙看甲」常是不同的位（例如一方感到「成」而另一方感到
「危」），两个方向分别读、绝不合并成一个分数。也可看**值日宿**的当日运。安坏禁判死刑、六害不
分级、不打分。

**Example.** [English](examples/xiuyao-en.md) · [中文](examples/xiuyao-zh.md)

**Requirements.** **Birth date only** — no birth hour, and no separate install if you already
installed the 八字 engine (宿曜 also uses `lunar-python`). For a two-person reading, both
people need a birth **date** in their birth-data files. Setup: [birth-data setup](chart-setup.md).

---

## 中西合参 East–West synthesis

**What it is.** 中西合参：把 natal / 八字 / 紫微 / 宿曜 多个体系放在一起综合解读（单人四系、
双人三轴）。编排只用 [`hecan/scripts/hecan_run.py`](../hecan/scripts/hecan_run.py)——**纯编排，
零新计算**：每个体系的盘都由它自己的脚本产出，hecan 只负责跨系阅读。两种模式：**共振模式**
（主题共振矩阵，默认推荐）或**全景模式**（各系全程 + 终章综合）。

**What to say.**

- 中文：*中西合参* · *合参* · *全体系解读* · *四盘合参* · *几个体系一起看* ·
  *我们俩中西合参*
- English: *"give me an East–West synthesis"* · *"read all my systems together"*

**What you get.** 一份跨体系综合：哪些体系在场、哪些缺席（**如实声明**——例如时辰未知时紫微跳过、
natal 12:00 降级、八字三柱），各系主题在哪里**呼应**、在哪里**分歧**。它的红线是**反多重宿命 +
禁投票**：当两个体系方向不一致时（比如八字说 A 承压、宿曜说 B 担险），它**不取多数、不抹平**，
而是并陈两条真实的层面。

**Example.** [English](examples/hecan-en.md) · [中文](examples/hecan-zh.md)

**Requirements.** Whatever the underlying systems need — so **Route A** for the Chinese
engines, plus your birth-data file(s). An unknown hour is handled by automatic degradation
(紫微 skipped, natal noon-flagged, 八字 three-pillar, 宿曜 unaffected). For a two-person
synthesis, create `birth-data-2.md` too. 紫微 has no two-person mode. Setup:
[birth-data setup](chart-setup.md).

---

*Next: [for developers](for-developers.md) — tests, evals, and conventions. Back to the
[README](../README.md).*
