# Astro-MBTI method（民俗游戏解读法）

## 与反翻译红线的关系 · Relationship to the anti-translation red line

`bazi/references/natal-bridge.md` 禁止占卜体系之间的符号翻译（没有元素对照表、没有
结构映射）。**本技能不违反该红线——类别不同，且四项资格条件全部满足**：反翻译红线管的
是**占卜体系↔占卜体系**的等价宣称——双方都宣称命运真相，翻译会伪造一种不存在的一一对应。
而 astro-mbti 的靶子是**世俗问卷**（MBTI，不宣称命运真相），并且同时满足四项**缺一不可**
的资格条件：①权重表全部公开；②同输入同输出、可证伪；③输出自带「不是测量」免责与
「请做正式测试」指引；④权重表是**民俗的编码**（documented folklore, scored），不是体系间
翻译。**缺任何一项，本节界定即不成立，红线照常适用**——后续功能不得只引「类别不同」而不
过这四道门。

反过来的义务：本技能**永不**宣称星盘与 MBTI 等价、永不把类型当诊断。若有人引用本
技能作为「体系可以翻译」的先例，指向本节：可以编码民俗并给它打分，**不可以**宣称两套
命运符号语言一一对应。

## 呈现顺序（强制 · mandated order）
1. **逐轴倾向（主体）**：每轴——倾向字母、置信度、驱动因子用人话（把 "Sun in
   Capricorn (earth)" 说成「你的摩羯太阳是土象——踏实、可验证的东西对你更可信」）。
2. **类型收尾彩蛋**：四字母 + 近平局亚军（若有）+ 免责块（原文引用，见下）。
3. **谱系脚注** + 「想知道真实类型请做正式测试」。

## Disclaimer 固定措辞（evals 逐字匹配；禁改写/省略/前移）
- EN: "This is a folklore game, not a measurement. Astrology→MBTI has no scientific
  correlation; if this feels accurate, research says that's self-attribution, not the
  stars. For your real type, take an actual MBTI instrument."
- 中文：「这是民俗游戏，不是测量。占星→MBTI 没有科学相关性；如果觉得准，研究表明那是
  自我归因，不是星星。想知道真实类型，请做正式的 MBTI 测试。」

## 权重表镜像 · Weight table mirror（真源：`scripts/mbti_score.py` 常量区）

票基础权重：Sun 2 · Moon 1.5 · ASC 1.5 · Mercury/Venus/Mars 各 1 · Jupiter/Saturn 各 0.5。
主相位 = 合/刑/冲/拱（六合不计）。相位组单位 0.75、封顶 1.5；角宫组单位 0.5、封顶 2。
**权重必须保持二进分数**（0.25 的整数倍）——净分才能精确累加，平局判定（净分=0）无浮点脆性。

| 轴 | 因子 | 方向 | 民俗出处 |
|---|---|---|---|
| E/I | 元素票：fire/air→E，earth/water→I | ±票权 | 流行民俗共识（火风外向/土水内向） |
| E/I | 角宫个人行星（1/4/7/10 宫） | E | 角宫=向外表达（民俗） |
| E/I | 地平线上（7–12 宫）个人行星过半 / 线下过半 | E / I | 半球强调（民俗） |
| E/I | Sun 落 1/5/7/10/11 宫 / 2/4/8/12 宫 | E / I | 宫位气质（民俗） |
| S/N | 元素票：earth→S，fire→N，air→0.5N，water→0.5S | ±票权 | 荣格四功能×元素；air 拆分是文档化抉择（经典荣格 air=thinking 归 T 吃大头；流行民俗 air=抽象 归 N 吃零头） |
| S/N | 天王/海王主相位到日月水（各 0.75，封顶 1.5） | N | 天海=直觉/越界（民俗） |
| S/N | 9/12 宫个人行星 ≥2 / 3/6 宫 ≥2 | N / S | 宫位抽象/务实轴（民俗） |
| T/F | 元素票：air→T，water→F，earth→0.5T，fire→0.5F | ±票权 | 荣格 air=thinking、water=feeling |
| T/F | 土星主相位到日月水（各 0.75，封顶 1.5） | T | 土星=结构/克制（民俗） |
| T/F | 月/金角宫或与水星主相位（各 0.75，共享封顶 1.5） | F | 月金=情感表达（民俗） |
| J/P | 模式票：cardinal→J，mutable→P，fixed→0.5J | ±票权 | 流行民俗；fixed 有争议故减权（文档化） |
| J/P | 土星主相位到日月（+1，二值） | J | 土星=秩序（民俗） |
| J/P | 木/海主相位到日月（各 0.75，封顶 1.5） | P | 木海=扩张/消融（民俗） |

**置信度语义**：`|净分|/满分`——high ≥ 0.5、medium ≥ 0.2、low < 0.2。置信度衡量的是
**民俗信号的强度**，永远不是「你真实类型的概率」。近平局（< 0.1×满分）→ 双显示
（「INTJ——或 INTP，T/P 接近五五开」）；完全平局（净分=0）→ 两字母并列显示，绝不装作笃定。
满分采用保守口径：拆分票轴（S/N、T/F）按整票权计满分，置信度略偏保守（文档化抉择）。

**`--json` 权威键名**（evals 以此为准；早期草案写作 `score` 的字段实为 `net`）：顶层
`type` / `runner_up` / `near_tie_axes` / `time_known` / `moon_ok` / `meta` / `degraded` /
`disclaimer`；每轴（`axes.EI|SN|TF|JP`）：`net`、`max`、`ratio`、`letter`、`confidence`、
`capped`、`near_tie`、`exact_tie`、`factors[]`（每项 `factor`/`toward`/`weight`）。

**时辰未知降级**：按 12:00 计算（承 davison noon-label 先例）；上升/宫位/角宫因子整组
剔除且满分同步缩小；E/I、J/P 置信度封顶 low；脚本 00:00/23:59 双算，当日月亮换座则
月亮因子整组剔除并标注。四字母照出 + 显式降级通告。（双采样足够的天文前提：月亮无逆行、
日行约 13°，单日至多穿越一次星座边界。）

## 零相关研究 · The null-correlation record（诚实框架的依据）
- Mayo, White & Eysenck (1978)：曾报告奇偶星座×外向性锯齿效应。
  https://doi.org/10.1080/00224545.1978.9924119
- van Rooij (1994)：效应只出现在**懂占星的被试**——自我归因机制，是文化回路不是出生
  效应。https://doi.org/10.1016/0191-8869(94)90243-7
- Carlson (1985, *Nature*)：双盲测试，占星师匹配星盘与人格档案不优于随机。
  https://doi.org/10.1038/318419a0
- Abdel-Khalek & Lester (2006)：跨文化（科威特/美国）零差异。
  https://doi.org/10.2466/pr0.98.2.602-607
- Pittenger (2005)：MBTI 本身的心理测量学问题（强制二分、重测漂移）——靶子也不稳。
  https://doi.org/10.1037/1065-9293.57.3.210

民俗谱系（为什么表「自洽」）：MBTI 源于荣格 1921《心理类型》，荣格四功能明引古典四
元素；流行民俗补全 E/I（火风/土水）与 J/P（基本/变动）。星座→类型对照（Leo=ENFP 类）
是纯 listicle，不入表。

## 红线（一票否决；其余承四系 voice-and-ethics 并集）
1. 类型永不回流为后续解读的前提或证据（禁「既然你是 INFJ…」）。
2. 禁等价/诊断措辞（「你就是」「测出」「你的真实类型是」）。
3. Disclaimer 不可省略、不可改写、不可前移冲淡。
4. 模型禁止绕过脚本手算权重表（无脚本环境 → 如实说明，无手动兜底）。
5. 近平局/完全平局必须双显示。

## 评测 · Evals

解读质量与红线遵守由 `astro-mbti/evals/README.md` 的确定性评测把关（expect 零手调
生成；三条诱饵追问覆盖对话级红线）。修改权重表、固定措辞或 fixtures 后，须按该 README
重新生成 expect 并重跑评测。
