---
name: hecan
description: 中西合参——natal/八字/紫微/宿曜 多体系综合解读（单人四系、双人三轴）。触发词：中西合参、合参、全体系解读、四盘合参、几个体系一起看。中文为主。
---

# 中西合参 Skill

## 流程

1. **问两次**：①单人还是双人合参；②共振模式（主题共振矩阵，默认推荐）还是全景模式
   （各系全程 + 终章综合）。
2. **输入**：读 `natal-astrology/birth-data.md`（甲方）与 `birth-data-2.md`（乙方，双人时）。
   时辰未知照常进行（脚本自动降级：紫微跳过、natal 12:00 降级标注、八字三柱、宿曜零降级）。
3. **编排**（模型永不自行逐系拼参数）：
   ```bash
   python hecan/scripts/hecan_run.py --year ... --hour <整数|unknown> --lon ... --lat ... \
     --tz ... --gender ... [--b-*同构] [--date YYYY-MM-DD] [--json]
   ```
   一次拿全部体系原生输出信封；个人化输出只落 stdout 或 gitignored `hecan/reports/`。
4. **解读**：按 `references/hecan-method.md`（所选模式）；各系输出按各自技能的 method
   文件理解；hooks 表只作主题呼应入口。
5. **红线**：hecan-method.md 红线四条（反多重宿命/禁投票/可用性如实/四系红线并集）一票否决。

## 边界

- 不做体系间翻译或符号对照（没有元素对照表、没有结构映射）。
- 紫微无双人模式；不做择日/化解。
- 各单系深度钻取请直接用对应技能（natal/bazi/ziwei/xiuyao）。
