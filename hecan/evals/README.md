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

## 文风 rubric（v4.1.0）

机械门禁先跑：

```bash
python3 scripts/prose_scan.py hecan/evals/runs
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

判定依据：`hecan/references/prose-style.md`。
