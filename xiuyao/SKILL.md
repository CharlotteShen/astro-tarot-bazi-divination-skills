---
name: xiuyao
description: 宿曜占星（二十七宿）——本命宿性格、双人三九相性、值日宿日运。触发词：宿曜、星宿、本命宿、二十七宿、宿曜相性、我们的宿。中文为主。只需出生日期，不需时辰。
---

# 宿曜占星 Skill

## 流程

1. **输入**：需要出生日期（公历年月日）。单人问性格/日运只要一人日期；
   双人相性要两人日期。可读 `natal-astrology/birth-data.md`（甲方）与
   `birth-data-2.md`（乙方）的 date 字段——**只取日期，时辰无关**。
2. **排宿**（模型永不数宿）：
   ```bash
   python xiuyao/scripts/xiuyao_chart.py --year YYYY --month M --day D \
     [--b-year YYYY --b-month M --b-day D] [--date YYYY-MM-DD] [--json]
   ```
   真实生辰仅经参数进内存；个人化输出只落 stdout 或 gitignored `xiuyao/reports/`。
3. **解读**：按 `references/method.md` 固定五步（含方向读法规则）；宿的性格材料查
   `references/mansions.md`（光影必须成对）。
4. **红线**：`references/voice-and-ethics.md` 总纲（危机应对/硬边界/隐私）+
   `references/method.md` 红线①–④（安坏禁判死刑、六害不分级≠灾祸、不打分、历法边界提示），
   一票否决。

## 边界

- 不推凌犯期间（需行星数据）；不做择日；28 宿变体不支持（正统 27 宿）。
- 与八字/紫微/西占的跨体系合参属 v3.4.0，本技能不主动联动。
