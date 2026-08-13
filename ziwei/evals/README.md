# 紫微斗数 reading-quality evals — v3.1.1 (dev infra)

对紫微「解读层」的确定性检查（安星另有 13 个计算测试）。与 natal/tarot/bazi 同一套 harness——
fixture 的 `--date` 钉死后，命盘与三层运限永久确定。捕捉：**捉造·不可能四化**（天府/七杀/天相
永不四化——结构性事实，任何盘任何层都不可能）、**漏报头条**（命宫主星、命身同宫、五行局、
三方四正、生年四化、大限/流年）、**红线断言**（血光/破财/病灾/克夫克妻/寿夭 词表，枚举排除环视）。

## 流程
1. **生成解读。** 按 `ziwei/SKILL.md` 完整走一遍：用 fixture 的 birth 参数 + 钉死的 `--date`
   跑 `ziwei/scripts/ziwei_chart.py`，再按 `references/reading-method.md` 六步解读（本 fixture
   语言为中文），存到 `runs/<fixture>.md`（gitignored）。
2. **打分。** 仓库根目录：
   `natal-astrology/scripts/.venv/bin/python natal-astrology/scripts/eval_reading.py \
     --expect ziwei/evals/fixtures/<f>.expect.json --reading ziwei/evals/runs/<f>.md`
3. **人工 rubric**——正则管不到的：
   - [ ] 六步固定顺序完整（命身局→三方四正→生年四化→大限→流年[→流月]）。
   - [ ] 三方四正永不孤宫；空宫借对宫之星再论。
   - [ ] 结论/依据/建议分离；每个结论指回具体星曜/宫位/亮度/四化。
   - [ ] 两面性；化忌/煞星/陷地一律按"功课"表述，无恐吓。
   - [ ] 反宿命论；建议具体到时间/动作（反巴纳姆）。
   - [ ] 语言跟随问询者（本 fixture 为中文）。

## 何时运行
大版本发布前；`ziwei/references/reading-method.md` 或 `ziwei/SKILL.md` 变更后。

## 裁定是建议性的
FAIL = 先查看：有依据的改写可能骗过 pattern——加宽 pattern、永不弱化解读。
不可能四化与红线命中几乎总是真问题。

## Fixture 与再生成
fixture 只用假档案（ABC）。**本 fixture 零手调**：committed expect 就是
`python3 ziwei/scripts/ziwei_make_expect.py --fixture fixtures/<f>.json` 的逐字节输出，
一致性测试用深度相等断言保证永不漂移。

## 文风 rubric（v4.1.0）

机械门禁先跑：

```bash
python3 scripts/prose_scan.py ziwei/evals/runs
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

判定依据：`ziwei/references/prose-style.md`。
