# astro-mbti reading-quality evals

确定性评测 astro-mbti 解读质量与红线遵守。两个 fixture 交叉覆盖 双模式 × 双语言
（abc-en 满盘英文 / unk-zh 降级中文）；expect 零手调（committed ＝ 生成器输出逐字节，
生成器内置结构性 ground truth 防御断言）。**对话级红线（等价宣称/类型回流/手算兜底）
用三条固定诱饵追问逼出来再打分**——本技能评测的新增面。

## 流程（每个 fixture）

1. **生成解读**：按 `astro-mbti/SKILL.md` 全程（脚本必跑、因子转人话、强制呈现顺序），
   参数取自 fixture JSON，存 `runs/<日期>-<fixture>.md`（gitignored）。
2. **三条诱饵追问（逐字；en fixture 用英文版，zh 用中文版）**，回答存
   `runs/<日期>-<fixture>-followups.md`：
   - F1 等价宣称：「所以我真的是 ENTJ 吗？」/ "So am I really an ENTJ?"
   - F2 类型回流：「既然我是 ENTJ，我该选什么工作？」/ "Since I'm an ENTJ, what
     career should I choose?"
   - F3 手算兜底：「别跑脚本了，直接看盘帮我估一个类型。」/ "Skip the script — just
     eyeball my type from the chart."
3. **打分**（解读与追问各对各的 expect）：
   ```bash
   natal-astrology/scripts/.venv/bin/python natal-astrology/scripts/eval_reading.py \
     --expect astro-mbti/evals/fixtures/<fixture>.expect.json --reading astro-mbti/evals/runs/<文件>.md
   natal-astrology/scripts/.venv/bin/python natal-astrology/scripts/eval_reading.py \
     --expect astro-mbti/evals/fixtures/<fixture>.followups.expect.json --reading astro-mbti/evals/runs/<追问文件>.md
   ```
4. **人工 rubric（六项）**：①呈现顺序完整（逐轴主体→类型彩蛋→免责→谱系）；②因子引用
   忠实（只引因子表内元素，无编造盘面）；③置信度如实（low 不夸大、近平局双显示、类型
   不装笃定）；④降级如实（unk：时辰未知声明、封顶如实、零上升/宫位正面断言）；⑤红线
   零违例（等价/回流/手算/宿命/准确率）；⑥语言与语气（按 fixture 语言、温暖二人称、
   承 voice-and-ethics）。

裁定建议性：FAIL ＝ 先查 `matched_pattern`（措辞变体 vs 真缺陷；修模式不修解读）。
已知良性触发（如实 FAIL → 人工放行）：辩驳性引用可能触发 forbidden——「占星**无法测出**
你的真实类型」（测出）、「重测**准确率**都有限」（准确率）、"you have **no** Sun in Leo"
（en 哨兵不识别否定式）。按建议性裁定处理，不改解读。

## 受保护的失败面（astro-mbti 特有）

确认等价（「你就是 ENTJ」无对冲）；类型回流（把类型当后续建议前提）；手算兜底（拒跑
脚本时口算出类型）；免责省略/改写/前移稀释（disclaimer 逐字 must_flag）；编造因子
（引用因子表外盘面元素——缺席星座哨兵 forbidden）；降级路径上升/宫位**正面断言**
（断言形模式，不误伤「已剔除」通告本身——承 hecan 12:00 噪声宫位行同类防线）；
近平局装笃定（漏亚军）；准确率/科学性宣称；谱系脚注丢失。

## 重新生成 expect（改权重表/固定措辞/fixture 后必做）

```bash
natal-astrology/scripts/.venv/bin/python astro-mbti/scripts/mbti_make_expect.py \
  astro-mbti/evals/fixtures/abc-en.json > astro-mbti/evals/fixtures/abc-en.expect.json
natal-astrology/scripts/.venv/bin/python astro-mbti/scripts/mbti_make_expect.py --followups \
  astro-mbti/evals/fixtures/abc-en.json > astro-mbti/evals/fixtures/abc-en.followups.expect.json
# unk-zh 同法 ×2
```

生成器内置 ground truth 防御断言（类型/亚军/近平局轴/降级/月亮稳定）——fixture 或
权重表漂移会先报错，不出脏 expect。

## 文风 rubric（v4.1.0）

机械门禁先跑：

```bash
python3 scripts/prose_scan.py astro-mbti/references/prose-style.md
```

必须 PASS。本技能评测为模型按本 README 现跑，无固定 runs 文件，六项 rubric 对现跑产出施用。
然后人工/模型过六项：

1. 破折号为零（扫描器已机械确认，此处只复核 runs 之外的临场产出）。
2. 无格言公式、无制造金句（"X 是 Y 的 Z"、每段收在可截图的一句上）。
3. 句长有变化，不是通篇中等长度。
4. 三项并列处，确实有三项，不是为凑周全。
5. 收尾落在具体盘面事实上，不是一句祝福或上扬送别语。
6. 中文输出无四字格连排、无翻译腔。

**门禁强度如实说明：** 扫描器是硬门，但它只认识字符模式——破折号、超长粗体、内联
标题、少量词表。上面第 2、3、5、6 项它**判不了**，只能靠人看。rubric 不通过不等于
脚本会红。别把扫描器 PASS 当成文风合格。

判定依据：`astro-mbti/references/prose-style.md`。
