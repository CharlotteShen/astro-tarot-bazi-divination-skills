# 宿曜 reading-quality evals

确定性评测宿曜**双人**解读质量。fixture 钉死（ABC×XYZ + `--date 2026-07-09`）→ ground truth
永久确定；expect 零手调（committed ＝ 生成器输出逐字节）。

## 流程

1. **生成**：按 `xiuyao/SKILL.md` 全程产出双人解读（fixture 参数 + 钉死 `--date`），
   存 `runs/<日期>-<标签>.md`（gitignored）。
2. **打分**：
   ```bash
   natal-astrology/scripts/.venv/bin/python natal-astrology/scripts/eval_reading.py \
     --expect xiuyao/evals/fixtures/xiuyao-pair.expect.json --reading xiuyao/evals/runs/<文件>.md
   ```
3. **人工 rubric（六项）**：五步齐全且不跳步；**方向读法正确**（谁承压/谁得成果与脚本输出
   一致）；光影成对；红线零违例（安坏判死刑/灾祸词/打分）；建议具体到时间/动作；语言中文。

裁定建议性：FAIL ＝ 先查看（可能是解读真缺陷，也可能是措辞变体——先读 `matched_pattern`）。

## 受保护的失败面

方向反转（甲乙看向颠倒）；捉造（心×虚≠安坏/荣亲/命、牛宿不存在）；漏报头条
（本命宿/双向相性/值日宿/六害位/历法边界）；红线（判死刑词表硬化环视，否定句/引用不误伤）。

## 重新生成 expect

```bash
natal-astrology/scripts/.venv/bin/python xiuyao/scripts/xiuyao_make_expect.py xiuyao/evals/fixtures/xiuyao-pair.json \
  > xiuyao/evals/fixtures/xiuyao-pair.expect.json
```
生成器内置防御断言（诱饵互斥/业胎距离None/六害钉死）——改 fixture 会先报错再要求重推 ground truth。
