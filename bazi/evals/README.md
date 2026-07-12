# 八字 reading-quality evals — v3.0.1 (dev infra)

对八字「解读层」的确定性检查（排盘另有 17 个计算测试）。与 `natal-astrology/evals/`、
`tarot/evals/` 同一套 harness——fixture 的 `--date` 钉死后，盘面（四柱/大运/流年/流月）永久
确定。捕捉：**捉造**（引用盘外干支）、**漏报头条**（不引柱、不下身强弱结论、漏当前大运/流年）、
**红线断言**（血光/破财/病灾/克夫克妻/寿夭 等 voice-and-ethics 禁语的可正则化子集）。

## 流程
1. **生成解读。** 按 `bazi/SKILL.md` 完整走一遍：用 fixture 的 birth 参数 + 钉死的 `--date`
   跑 `bazi/scripts/bazi_chart.py`，再按 `references/reading-method.md` 五步解读（本 fixture
   语言为中文），存到 `runs/<fixture>.md`（本目录 gitignored）。
2. **打分。** 仓库根目录下：
   `natal-astrology/scripts/.venv/bin/python natal-astrology/scripts/eval_reading.py \
     --expect bazi/evals/fixtures/<f>.expect.json --reading bazi/evals/runs/<f>.md`
   （grader 纯 stdlib，任意 `python3` 皆可。）Exit 0 = 全部通过。
3. **人工 rubric**——正则管不到的：
   - [ ] 五步固定顺序完整（排盘→身强弱→喜用神→大运→流年[→流月]）。
   - [ ] 结论/依据/建议分离；每个结论指回脚本输出的具体干支/十神。
   - [ ] 两面性；矛盾并陈后裁决。
   - [ ] 反宿命论；无医疗/法律/财务/寿夭断言（词表只捕捉最露骨的）。
   - [ ] 建议具体到时间/动作（反巴纳姆）。
   - [ ] 语言跟随问询者（本 fixture 为中文）。

## 何时运行
大版本发布前；`bazi/references/reading-method.md` 或 `bazi/SKILL.md` 变更后。

## 裁定是建议性的
FAIL = 先查看：有依据的改写可能骗过 pattern——加宽 pattern、永不弱化解读。
捉造与红线命中几乎总是真问题。

## Fixture 与再生成
fixture 只用假档案（ABC）。期望骨架由
`python3 bazi/scripts/bazi_make_expect.py --fixture fixtures/<f>.json` 生成（重算钉死盘面，stdout
输出），手调后提交；`test_bazi_make_expect.py` 的一致性测试保证提交的期望与钉死盘面永不漂移。
身强弱判定入档：三得法两得一失 + 打分法同党 74% → 身强。
