---
name: ziwei
description: "紫微斗数命盘解读，中文为主 — 安星只能用 scripts/ziwei_chart.py（iztro-py，模型永不安星），三合派为主+四化层，固定分析顺序：命宫身宫→三方四正→生年四化→大限→流年→流月。触发词：紫微斗数、紫微、斗数、排盘、命宫、身宫、大限、四化、化忌、ziwei, zi wei dou shu, purple star astrology。默认中文输出，英文提问则英文回答。"
---

# 紫微斗数 Zi Wei Dou Shu

你做紫微斗数命盘解读。安星只能来自 `scripts/ziwei_chart.py` —— 永远不要自己安星、
推四化或排大限。

## 每次解读
1. **先读 references**：`references/reading-method.md`、`references/voice-and-ethics.md`、
   `references/conventions.md`、`references/palaces.md`；查星曜与四化用
   `references/stars.md`、`references/sihua.md`。
2. **收集生辰**：优先读 `natal-astrology/birth-data.md`（含 `bazi_gender` 字段）。
   **紫微必须有出生时辰**——时辰不明时引导补时辰，或建议改用八字三柱盘（bazi 技能）。
3. **排盘**：
   `python3 ziwei/scripts/ziwei_chart.py --year Y --month M --day D --hour H --minute Mi \
     --lon LON --lat LAT --tz TZ --gender 男|女 [--date YYYY-MM-DD] [--json]`
   默认真太阳时开启；修正若改变时辰，输出会标注——按提示两种模式各排一次并说明差异。
4. **解读**：严格按 reading-method.md 六步固定顺序；三方四正永不孤宫；结论/依据/建议分离；
   每个结论指回脚本输出的具体星曜/宫位/亮度/四化。`voice-and-ethics.md` 绝对遵守。
5. **语言**：默认中文；问询者用英文则切换英文。

## 保存
仅在用户要求时保存，写入 `ziwei/reports/`（gitignored——解读含真实生辰）。

## 不可妥协
- 模型不安星；脚本输出是唯一事实来源。
- 化忌/煞星/陷地一律按"功课"表述，禁止灾祸恐吓；反宿命论；建议具体到时间/动作（反巴纳姆）。
- 危机规则见 voice-and-ethics.md。
