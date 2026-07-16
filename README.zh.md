# astro-tarot-bazi-divination-skills

**七种命理 · 一套工具。** 为 [Claude Code](https://claude.com/claude-code) 打造的七个命理技能：
西洋本命占星、塔罗、八字、紫微斗数、宿曜占星、一套中西合参的东西方综合解读，以及星盘测 MBTI
民俗游戏。所有计算都是确定性的、由脚本完成——行星位置、排盘、抽牌、四轴打分都来自带种子/经过校验
的代码，绝不出自模型的凭空想象——好让 AI 去做它真正擅长的事：**解读**。中文 + English。

[English → README.md](README.md)

> 仅供自我觉察与娱乐；不构成医疗、法律或财务建议。

## 它能做什么？

| 技能 | 你说 | 尝一口 |
|---|---|---|
| 🌌 **natal-astrology** | *「读我的星盘」* | ["The arc of your chart is a movement from *carrying* to *shining*."](docs/examples/natal-astrology-en.md) —— *你星盘的弧线，是一场从"承担"走向"闪耀"的旅程* |
| 🃏 **tarot** | *「抽张塔罗牌」* | ["gather the scattered power before spending it"](docs/examples/tarot-en.md) —— *先把散落的力量聚拢，再谈动用* |
| 🀄 **bazi 八字** | *「看看我的八字」* | [「积累有余、产出不足」](docs/examples/bazi-zh.md) |
| 🏮 **ziwei 紫微斗数** | *「排个紫微盘」* | [「被点名的地方，正是今年最值得下功夫的地方。」](docs/examples/ziwei-zh.md) |
| 🌙 **xiuyao 宿曜** | *「我的本命宿」* | [「ABC 觉得是在得成果，XYZ 觉得是在冒风险」](docs/examples/xiuyao-zh.md) |
| ☯️ **hecan 中西合参** | *「中西合参」* | [「你以为你在让步，对方可能觉得他在冒险」](docs/examples/hecan-zh.md) |
| 🎭 **astro-mbti** | *「星盘测 MBTI」* | [「这是民俗游戏，不是测量」](docs/examples/astro-mbti-zh.md) |

每个技能的深入指南：[docs/skills-guide.md](docs/skills-guide.md)

## 你需要什么

- 一台带终端机的电脑（macOS、Linux，或 Windows + WSL）
- 一个 [Claude](https://claude.ai) 订阅（Claude Code 随订阅附带）
- Python 3 —— **可选**（仅"路线 A"本地排盘需要；"路线 B"直接从 astro.com 粘贴星盘即可，完全不用
  Python）

## 快速开始

**1. 安装 Claude Code**（已经装了就跳过）：

```bash
npm install -g @anthropic-ai/claude-code   # or see https://docs.claude.com/claude-code
claude   # run once, sign in
```

**2. 克隆本仓库并安装技能：**

```bash
git clone https://github.com/CharlotteShen/astro-tarot-bazi-divination-skills.git
cd astro-tarot-bazi-divination-skills
./install.sh
```

`install.sh` 会把七个技能软链接进 `~/.claude/skills/`，并询问是否安装 Python 排盘引擎、是否为你
创建私人的出生数据文件。（`./install.sh --copy` 改为复制而非软链接；`./install.sh --uninstall`
移除这些链接。）

<details>
<summary>想手动来？下面就是 <code>install.sh</code> 所做的每一步。</summary>

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

如果 `pip install` 报 `externally-managed-environment`，请改用虚拟环境——见
[docs/chart-setup.md → 路线 A](docs/chart-setup.md#if-pip-install-fails-with-externally-managed-environment)。
</details>

**3. 设置你的出生数据** —— 填写 `natal-astrology/birth-data.md`（install.sh 会提示帮你创建）。
两条路线、完整指南见 [docs/chart-setup.md](docs/chart-setup.md)。它只留在你自己的机器上
（已被 gitignore）。塔罗不需要出生数据——可以直接跳到抽牌。

**4. 第一次解读** —— 开一个**新的** Claude Code 会话，直接说：

```
read my chart          → whole-chart synthesis
看看我的八字            → 八字 four-pillars reading
draw me a tarot card   → works even without birth data
```

你从不需要点名调用某个技能——用平常的中文或英文说出你想要什么，对应的技能就会自己醒来。

## 可以问什么

每个技能的入门速查（中文 + English）。完整清单、以及每种解读会返回什么，都在
[docs/skills-guide.md](docs/skills-guide.md)。

**🌌 natal-astrology** —— 整盘综观、逐星细读、预测套件、关系合盘、星盘图
- 中文：*本命盘* · *我的月亮是什么意思* · *行运* · *流年* · *太阳返照* · *二次推运* · *画个星盘* · *合盘*
- English: *"read my chart"* · *"tell me about my Venus"* · *"what does my Saturn mean for money"* · *"what are my transits"* · *"what's coming up this year"* · *"show my chart wheel"* · *"compare my chart with theirs"*

**🃏 tarot** —— 七种牌阵、带种子可复现的抽牌、无需出生数据
- 中文：*抽一张牌* · *三张牌看看这段关系* · *帮我起个牌阵* · *凯尔特十字* · *每日一牌*
- English: *"draw me a tarot card"* · *"do a three-card spread on my job"* · *"tarot reading about this decision"* · *"pull a Celtic Cross"* · *"daily card"*

**🀄 bazi 八字** —— 四柱排盘 → 身强弱 → 喜用神 → 大运 → 流年 → 流月，也支持合八字
- 中文：*八字* · *批八字* · *排个盘看看* · *我的大运* · *今年流年怎么样* · *喜用神* · *合八字*
- English: *"read my BaZi / four pillars"* · *"what's my day master"* · *"my luck cycle this year"*

**🏮 ziwei 紫微斗数** —— 命宫身宫 → 三方四正 → 生年四化 → 大限 → 流年 → 流月
- 中文：*紫微斗数* · *排个紫微盘* · *我的命宫* · *身宫* · *大限* · *我的化忌在哪* · *今年流年*
- English: *"read my Zi Wei Dou Shu / purple star chart"*

**🌙 xiuyao 宿曜** —— 本命宿性格 · 双人三九相性（双向并陈）· 值日宿日运，只需出生日期
- 中文：*宿曜* · *我的本命宿* · *宿曜相性* · *我们的宿合不合* · *今天的值日宿*
- English: *"what's my xiuyao / birth mansion"* · *"our xiuyao compatibility"*

**☯️ hecan 中西合参** —— 多体系综合，单人四系 / 双人三轴（共振模式或全景模式）
- 中文：*中西合参* · *合参* · *四盘合参* · *几个体系一起看* · *我们俩中西合参*
- English: *"give me an East–West synthesis"* · *"read all my systems together"*

**🎭 astro-mbti** —— 星盘测 MBTI 民俗游戏：逐轴倾向+置信度为主体，四字母类型仅供娱乐（需要 natal-astrology 技能 + Python）
- 中文：*星盘测 MBTI* · *占星 MBTI* · *我的星盘是什么 MBTI*
- English: *"predict my MBTI from my chart"* · *"what MBTI does my chart suggest"*

## 隐私

你的 `birth-data.md`（以及任何第二人档案、已保存的解读、生成的报告）都已被 **gitignore** ——
即便你 fork 并 push 本仓库，它们也绝不会离开你的机器。被追踪的文件树里只有虚构的测试档案
（ABC / XYZ / UNK）。每条 `.gitignore` 规则各自保护什么，详见
[docs/chart-setup.md → 隐私](docs/chart-setup.md#privacy-what-stays-on-your-machine)。

**让防护机制持续生效的两个习惯：**

- **把个人信息填在模板的 `- 字段:` 行里**，放进 `birth-data.md` / `birth-data-2.md`，并让生成的
  内容落进被 gitignore 的 `reports/`、`charts/`、`readings/` 目录。这些文件名和字段正是
  `.gitignore` 所保护、也是本仓库隐私扫描器所识别的对象。若把真实信息写进*其它*文件、或改名后的
  数据文件，二者都无法覆盖。拿不准时，提交前先跑一下 `git status`：你的出生数据绝不该出现在里面。
- **要贡献改动？新文件名请用 ASCII。** 发布工具按字面匹配被追踪的文件路径，非 ASCII 文件名可能
  触发它的安全检查误报（见 [docs/for-developers.md](docs/for-developers.md)）。

## 约定与致谢

各体系方法均遵循标准/公认参考（回归黄道、默认 Placidus 分宫、Swiss Ephemeris 经
[kerykeion](https://github.com/g-battaglia/kerykeion) 计算；八字/宿曜经 lunar-python；紫微经 iztro-py）；
少数容许度/阈值属于可调的约定选择——清单见
[docs/for-developers.md](docs/for-developers.md#conventions-so-you-know-whats-a-choice)。

## 面向开发者

测试、解读质量评估、以及贡献说明：[docs/for-developers.md](docs/for-developers.md)

## 许可证

[MIT](LICENSE) © 2026 Charlotte Shen
