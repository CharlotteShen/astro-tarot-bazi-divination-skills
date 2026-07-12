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
