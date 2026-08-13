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

## 文风 rubric（v4.1.0）

机械门禁先跑：

```bash
python3 scripts/prose_scan.py xiuyao/evals/runs
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

判定依据：`xiuyao/references/prose-style.md`。
