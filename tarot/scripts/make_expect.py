"""Expectation-skeleton generator for tarot eval fixtures — re-draws the fixture's pinned seed
(ground truth: seeded draws are deterministic forever) and emits a must_mention/forbidden skeleton
to stdout. The author hand-tunes the output, then commits it (same "authored from verified script
output" provenance as the natal fixtures). Pure stdlib; like draw.py, never writes files.
"""
import argparse
import json
import os
import sys

from draw import draw_spread

CARDS_MD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                        "references", "cards.md")

# Fabrication decoys: distinctive multi-word majors only. Common-word majors (Death, Strength,
# Justice, The Sun/Moon/Star) can appear in grounded prose without citing the card. The Lovers
# sits last — 恋人 is everyday vocabulary in relationship questions; drop it when hand-tuning those.
SALIENT = ["The Tower", "Wheel of Fortune", "The Hanged Man",
           "The High Priestess", "The Devil", "The Lovers"]

# reading-method.md names this advice as banned verbatim — regexable, so graded. But the grader only
# sees raw text, so a reading that *refuses* the cliché ("I will not tell you to just trust your
# intuition") or *quotes* it ("not a 'stay balanced' kind of reading") would trip a naive substring
# match. Guard every phrase so it counts only when handed out as advice: anchor at the clause start
# and refuse to cross a negation word or quote mark on the way to the phrase. Python's re has no
# variable-width lookbehind and the negation can sit several words ahead of the phrase, so a fixed
# lookbehind can't see it — hence the clause-anchored tempered dot. Residual forms (a negation in an
# earlier clause, rhetorical quotation with no cue) leak to the human rubric — same tradeoff as
# bazi's 红线 enumeration guard.
_CLAUSE_START = r"(?:^|[.!?;。！？；\n])"
_DISCLAIM_CUE = (r'''(?:\b(?:not|no|never|cannot|without)\b|n't|'''
                 r'''[不别無无非]|["'“”‘’「」『』《》])''')


def _asserted(core: str) -> str:
    """Match a Barnum phrase only where it is *dispensed as advice* — i.e. no negation or quote mark
    stands between the start of its clause and the phrase (so a disclaimer or quotation that names the
    cliché to reject it is left for the human rubric). ``core`` is a non-capturing-safe sub-pattern."""
    return rf"(?i){_CLAUSE_START}(?:(?!{_DISCLAIM_CUE}).)*?(?:{core})"


BARNUM = [
    {"desc": "Barnum: trust your intuition",
     "patterns": [_asserted(r"trust your (?:intuition|gut)"), _asserted(r"相信(?:你的)?直觉")]},
    {"desc": "Barnum: it will work out",
     "patterns": [_asserted(r"it will (?:all )?work out"),
                  _asserted(r"everything will (?:be fine|work out)"),
                  _asserted(r"一切都?会好起来"), _asserted(r"顺其自然")]},
    {"desc": "Barnum: stay balanced",
     "patterns": [_asserted(r"stay balanced"), _asserted(r"保持平衡")]},
    {"desc": "Barnum: communicate more",
     "patterns": [_asserted(r"communicate more"), _asserted(r"多沟通")]},
]


def load_zh_names() -> dict:
    """EN → 中文 card names from the references/cards.md pipe table."""
    zh = {}
    with open(CARDS_MD, encoding="utf-8") as f:
        for line in f:
            if line.startswith("|") and "---" not in line and not line.startswith("| #"):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) == 8:
                    zh[cells[1]] = cells[2]
    return zh


def _short(card: str) -> str:
    return card[4:] if card.startswith("The ") else card


# Deck names are letters and spaces only (test_cards_md_structure pins them to draw.py's DECK),
# so they are embedded in regexes unescaped — re.escape would escape the spaces (Python 3.7+).
def card_patterns(card: str, zh_name: str) -> list:
    pats = [rf"(?i)\b{card.lower()}\b"]
    if card.startswith("The "):
        pats.append(rf"(?i)\b{_short(card).lower()}\b")
    pats.append(zh_name)
    return pats


def reversal_patterns(card: str, zh_name: str) -> list:
    s = _short(card).lower()
    return [rf"(?i){s}[^.]{{0,80}}(revers|blocked|inward|overdone)",
            rf"(?i)revers[^.]{{0,60}}{s}",
            rf"{zh_name}[^。]{{0,40}}逆位",
            rf"逆位[^。]{{0,20}}{zh_name}"]


def build_expect(fx: dict) -> dict:
    seed = int(fx["seed"])  # a quoted "15" would seed the RNG from the string hash — a different draw
    cards = draw_spread(fx["spread"], seed)
    zh = load_zh_names()
    drawn = {c["card"] for c in cards}

    must = []
    for c in cards:
        must.append({"desc": f"{c['position']}: {c['card']} ({c['orientation']})",
                     "patterns": card_patterns(c["card"], zh[c["card"]])})
        if c["orientation"] == "reversed":
            must.append({"desc": f"reversal read: {c['card']}",
                         "patterns": reversal_patterns(c["card"], zh[c["card"]])})
    must.append({"desc": f"seed {seed} shown",
                 "patterns": [rf"(?i)seed\D{{0,10}}{seed}\b",
                              rf"种子\D{{0,10}}{seed}"]})

    fabricated = [{"desc": f"fabricated: {name}",
                   "patterns": [rf"(?i)\b{name.lower()}\b", zh[name]]}
                  for name in SALIENT if name not in drawn][:3]
    return {"reading_type": "tarot", "must_mention": must,
            "forbidden": fabricated + BARNUM, "must_flag": []}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Emit an expect.json skeleton for a tarot eval fixture "
                    "(stdout; hand-tune, then commit).")
    ap.add_argument("--fixture", required=True,
                    help="fixture input JSON (spread/seed/question/language)")
    args = ap.parse_args(argv)
    try:
        with open(args.fixture, encoding="utf-8") as f:
            fx = json.load(f)
        expect = build_expect(fx)
    except Exception as e:  # noqa: BLE001 — clean message, no traceback
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print(json.dumps(expect, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
