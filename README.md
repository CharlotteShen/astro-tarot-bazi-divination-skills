# astro-tarot-bazi-divination-skills

**七种命理 · One toolkit.** Seven divination skills for [Claude Code](https://claude.com/claude-code):
Western natal astrology, tarot, 八字 BaZi, 紫微斗数 Zi Wei Dou Shu, 宿曜占星, a 中西合参
East-meets-West synthesis, and an astro-MBTI folklore game. All calculation is deterministic and
scripted — planetary positions, 排盘, card draws, axis scores come from seeded/verified code, never
from the model's imagination — so the AI does what it's actually good at: **interpretation**.
English + 中文.

[中文说明 → README.zh.md](README.zh.md)

> For self-reflection and entertainment; not medical, legal, or financial advice.

## What can it do?

| Skill | You say | A taste |
|---|---|---|
| 🌌 **natal-astrology** | *"read my chart"* | ["The arc of your chart is a movement from *carrying* to *shining*."](docs/examples/natal-astrology-en.md) |
| 🃏 **tarot** | *"draw me a tarot card"* | ["gather the scattered power before spending it"](docs/examples/tarot-en.md) |
| 🀄 **bazi 八字** | *「看看我的八字」* | [「积累有余、产出不足」](docs/examples/bazi-zh.md) — *plenty of accumulation, too little production* |
| 🏮 **ziwei 紫微斗数** | *「排个紫微盘」* | [「被点名的地方，正是今年最值得下功夫的地方。」](docs/examples/ziwei-zh.md) — *the named spot is exactly where the year's effort is best spent* |
| 🌙 **xiuyao 宿曜** | *「我的本命宿」* | [「ABC 觉得是在得成果，XYZ 觉得是在冒风险」](docs/examples/xiuyao-zh.md) — *same relationship, felt in opposite ways* |
| ☯️ **hecan 中西合参** | *「中西合参」* | [「你以为你在让步，对方可能觉得他在冒险」](docs/examples/hecan-zh.md) — *you think you're giving way; the other feels they're taking a risk* |
| 🎭 **astro-mbti** | *"predict my MBTI from my chart"* | ["**ENTJ** — or ENFJ (T/F near 50/50)"](docs/examples/astro-mbti-en.md) — *a folklore game, not a measurement* |

Deeper guide to every skill: [docs/skills-guide.md](docs/skills-guide.md)

## What you need

- A computer with a terminal (macOS, Linux, or Windows + WSL)
- A [Claude](https://claude.ai) subscription (Claude Code comes with it)
- Python 3 — **optional** (only for "Route A" local chart calculation; "Route B" works by
  pasting your chart from astro.com, no Python at all)

## Quickstart

**1. Install Claude Code** (skip if you have it):

```bash
npm install -g @anthropic-ai/claude-code   # or see https://docs.claude.com/claude-code
claude   # run once, sign in
```

**2. Clone this repo & install the skills:**

```bash
git clone https://github.com/CharlotteShen/astro-tarot-bazi-divination-skills.git
cd astro-tarot-bazi-divination-skills
./install.sh
```

`install.sh` symlinks the seven skills into `~/.claude/skills/`, offers to install the Python
calculation engines, and offers to create your private birth-data file. (`./install.sh --copy`
copies instead of symlinking; `./install.sh --uninstall` removes the links.)

<details>
<summary>Prefer to do it by hand? Here's exactly what <code>install.sh</code> does.</summary>

```bash
# 1. link the seven skill folders into your Claude Code skills directory
mkdir -p ~/.claude/skills
for s in natal-astrology tarot bazi ziwei xiuyao hecan astro-mbti; do
  ln -s "$PWD/$s" ~/.claude/skills/"$s"
done

# 2. (optional — Route A only) install the calculation engines
#    kerykeion (astrology) · lunar-python (八字 + 宿曜) · iztro-py (紫微)
pip install -r natal-astrology/scripts/requirements.txt \
            -r bazi/scripts/requirements.txt \
            -r ziwei/scripts/requirements.txt

# 3. create your private birth-data file from the template (gitignored)
cp natal-astrology/birth-data.template.md natal-astrology/birth-data.md
```

If `pip install` reports `externally-managed-environment`, use a virtual environment — see
[docs/chart-setup.md → Route A](docs/chart-setup.md#if-pip-install-fails-with-externally-managed-environment).
</details>

**3. Set up your birth data** — fill `natal-astrology/birth-data.md` (install.sh offers to create
it). Two routes, full guide: [docs/chart-setup.md](docs/chart-setup.md). It stays on your
machine (gitignored). Tarot needs no birth data — you can skip straight to a draw.

**4. First reading** — open a NEW Claude Code session and just say:

```
read my chart          → whole-chart synthesis
看看我的八字            → 八字 four-pillars reading
draw me a tarot card   → works even without birth data
```

You never call a skill by name — say what you want in plain English or 中文, and the matching
skill wakes up on its own.

## What to ask

A starter cheat-sheet per skill (English + 中文). The full list, and what each reading returns,
is in [docs/skills-guide.md](docs/skills-guide.md).

**🌌 natal-astrology** — whole-chart, per-planet, the predictive suite, relationship charts, wheels
- English: *"read my chart"* · *"tell me about my Venus"* · *"what does my Saturn mean for money"* · *"what are my transits"* · *"what's coming up this year"* · *"show my chart wheel"* · *"compare my chart with theirs"*
- 中文：*本命盘* · *我的月亮是什么意思* · *行运* · *流年* · *太阳返照* · *二次推运* · *画个星盘* · *合盘*

**🃏 tarot** — seven spreads, seeded reproducible draws, no birth data required
- English: *"draw me a tarot card"* · *"do a three-card spread on my job"* · *"tarot reading about this decision"* · *"pull a Celtic Cross"* · *"daily card"*
- 中文：*抽一张牌* · *三张牌看看这段关系* · *帮我起个牌阵* · *凯尔特十字* · *每日一牌*

**🀄 bazi 八字** — 四柱排盘 → 身强弱 → 喜用神 → 大运 → 流年 → 流月，也支持合八字
- 中文：*八字* · *批八字* · *排个盘看看* · *我的大运* · *今年流年怎么样* · *喜用神* · *合八字*
- English: *"read my BaZi / four pillars"* · *"what's my day master"* · *"my luck cycle this year"*

**🏮 ziwei 紫微斗数** — 命宫身宫 → 三方四正 → 生年四化 → 大限 → 流年 → 流月
- 中文：*紫微斗数* · *排个紫微盘* · *我的命宫* · *身宫* · *大限* · *我的化忌在哪* · *今年流年*
- English: *"read my Zi Wei Dou Shu / purple star chart"*

**🌙 xiuyao 宿曜** — 本命宿性格 · 双人三九相性（双向并陈）· 值日宿日运，只需出生日期
- 中文：*宿曜* · *我的本命宿* · *宿曜相性* · *我们的宿合不合* · *今天的值日宿*
- English: *"what's my xiuyao / birth mansion"* · *"our xiuyao compatibility"*

**☯️ hecan 中西合参** — 多体系综合，单人四系 / 双人三轴（共振模式或全景模式）
- 中文：*中西合参* · *合参* · *四盘合参* · *几个体系一起看* · *我们俩中西合参*
- English: *"give me an East–West synthesis"* · *"read all my systems together"*

**🎭 astro-mbti** — MBTI-from-chart folklore game: per-axis leanings + confidence first, four-letter type for fun only (needs the natal-astrology skill + Python)
- English: *"predict my MBTI from my chart"* · *"what MBTI does my chart suggest"*
- 中文：*星盘测 MBTI* · *占星 MBTI* · *我的星盘是什么 MBTI*

## Privacy

Your `birth-data.md` (and any second-person file, saved readings, generated reports) are
**gitignored** — they never leave your machine even if you fork and push this repo. The tracked
tree contains only fictional test profiles (ABC / XYZ / UNK). What each `.gitignore` pattern
protects is spelled out in
[docs/chart-setup.md → Privacy](docs/chart-setup.md#privacy-what-stays-on-your-machine).

**Two habits that keep the guardrails working:**

- **Keep personal details in the template's `- field:` lines**, inside `birth-data.md` /
  `birth-data-2.md`, and let generated output land in the gitignored `reports/`, `charts/`, and
  `readings/` folders. Those filenames and fields are exactly what `.gitignore` protects — and
  what the repo's privacy scanner recognizes. Real details typed into some *other* file, or a
  renamed data file, would not be covered. When in doubt, run `git status` before committing: your
  birth data should never appear.
- **Contributing a change? Keep new filenames ASCII.** The publish tooling matches tracked file
  paths literally, so a non-ASCII filename can trip its safety check (see
  [docs/for-developers.md](docs/for-developers.md)).

## Conventions & credits

Methods follow standard/verified references (tropical zodiac, Placidus default, Swiss Ephemeris via
[kerykeion](https://github.com/g-battaglia/kerykeion); 八字/宿曜 via lunar-python; 紫微 via iztro-py);
a few orb/threshold choices are tunable conventions — the list lives in
[docs/for-developers.md](docs/for-developers.md#conventions-so-you-know-whats-a-choice).

## For developers

Tests, reading-quality evals, and contribution notes: [docs/for-developers.md](docs/for-developers.md)

## License

[MIT](LICENSE) © 2026 Charlotte Shen
