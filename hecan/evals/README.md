# 合参 reading-quality evals

确定性评测**合参**解读质量（共振模式）。fixture 钉死（ABC×UNK 一方时辰未知 +
`--date 2026-07-09`）→ 可用性矩阵成为结构性 ground truth（紫微恒 skipped、natal 恒
degraded）；expect 零手调（committed ＝ 生成器输出逐字节，生成器直接跑编排器自维护）。

## 流程

1. **生成**：按 `hecan/SKILL.md` 全程（共振模式）产出双人合参解读（fixture 参数 +
   钉死 `--date`），存 `runs/<日期>-<标签>.md`（gitignored）。
2. **打分**：
   ```bash
   natal-astrology/scripts/.venv/bin/python natal-astrology/scripts/eval_reading.py \
     --expect hecan/evals/fixtures/hecan-pair.expect.json --reading hecan/evals/runs/<文件>.md
   ```
3. **人工 rubric（六项）**：共振模式四步齐全；各系发声与信封一致；共振与分歧并陈；
   **缺席/降级如实**（声明紫微缺席与宫位不可用，且不引用）；红线零违例
   （投票/翻译/宿命/词表）；建议具体到时间/动作、语言中文。

裁定建议性：FAIL ＝ 先查看 `matched_pattern`（措辞变体 vs 真缺陷）。

## 受保护的失败面（合参特有）

引用缺席体系（紫微星曜/宫位正面断言；降级 natal 的上升/宫位重叠断言——注意
degraded 信封原文里仍含 12:00 噪声宫位行，诱饵正是防误读它们）；一致性投票
（「N 个体系都…所以更…」）；翻译对照（五行↔元素、十神↔行星等式）；多重宿命
（命更硬/印证注定）；宿曜方向反转；漏报（本命宿/各轴真 token/缺席声明/共振与分歧）。

## 重新生成 expect

```bash
natal-astrology/scripts/.venv/bin/python hecan/scripts/hecan_make_expect.py hecan/evals/fixtures/hecan-pair.json \
  > hecan/evals/fixtures/hecan-pair.expect.json
```
生成器内置可用性矩阵防御断言——改 fixture（如把 unknown 换成整数时辰）会先报错。
