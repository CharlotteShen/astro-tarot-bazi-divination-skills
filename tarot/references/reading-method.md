# Reading method

## Before drawing
A vague question gets ONE clarifying exchange ("what decision is this actually about?"). Anchor the
reading to something concrete the querent said, and return to that anchor in the synthesis.

## The draw
Run `scripts/draw.py --spread <key> [--question "..."]`. The model NEVER picks cards. Show the spread
name, each position/card/orientation, and the **seed** (any reading can be reproduced with
`--seed <n>`).

## Per card, in position
Meaning = card keywords (`cards.md`) × position meaning (`spreads.md`) × the actual question. The same
card must read differently in different positions and questions — a generic card lecture is the tarot
version of the cookbook failure. Reversals read as the energy turned inward, blocked, or overdone — not
as simple "bad".

## The whole-spread layer (any spread ≥3 cards — never skip)
- **Suit/element distribution:** a dominant suit names the arena (Wands/fire = drive & venture, Cups/
  water = feeling & relating, Swords/air = thought & conflict, Pentacles/earth = body, work & money);
  an absent suit names the blind spot.
- **Majors ratio:** mostly majors → a pivotal chapter, bigger than day-to-day; mostly minors → everyday
  choices dominate — say so, and hand the agency back.
- **Reversal density:** many reversals → the energy is internalized, blocked, or in revision; read the
  whole spread more gently and inwardly.
- **Interactions:** read neighboring/axis positions as conversations, not islands.

## Synthesis
One narrative — beginning, tension, turn, and an ending that lands on a **concrete next step tied to a
time or action** ("draft the message tonight; send it before Friday"). Forbidden: "communicate more",
"trust your intuition", "stay balanced", "it will work out" — if the advice fits anyone, it's not a
reading (反巴纳姆：建议必须具体到时间/动作).

## Natal bridge (optional — only if birth data exists AND the querent opts in)
If `natal-astrology/birth-data.md` exists, you may OFFER (once): cards carry traditional astrological
correspondences (`cards.md` Astro column) — at most 1–2 resonance notes per reading, e.g. "The Emperor
↔ Aries — your rising sign; this card is speaking in your first language." Supporting color only; never
required, never steering. Pure tarot stays pure.

## Language
EN or 中文 following the querent; 中文 card names from `cards.md`.
