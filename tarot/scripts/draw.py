"""Tarot draw script — the ONLY way cards are drawn (the model never picks cards).
Uniform random, no repeats, 50/50 reversals, seed always printed for reproducibility.
Pure stdlib. The --question is echoed to stdout only; this script never writes files.
"""
import argparse
import json
import random
import secrets
import sys

MAJORS = ["The Fool", "The Magician", "The High Priestess", "The Empress", "The Emperor",
          "The Hierophant", "The Lovers", "The Chariot", "Strength", "The Hermit",
          "Wheel of Fortune", "Justice", "The Hanged Man", "Death", "Temperance",
          "The Devil", "The Tower", "The Star", "The Moon", "The Sun", "Judgement", "The World"]
RANKS = ["Ace", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
         "Page", "Knight", "Queen", "King"]
SUITS = ["Wands", "Cups", "Swords", "Pentacles"]
DECK = MAJORS + [f"{r} of {s}" for s in SUITS for r in RANKS]

SPREADS = {
    "single": ("Single Card", ["Guidance"]),
    "three": ("Three-Card", ["Past", "Present", "Future"]),
    "relationship": ("Relationship", ["You", "The other", "The connection",
                                      "The challenge", "Direction"]),
    "decision": ("Decision", ["Heart of the matter", "Path A", "Path B",
                              "What you're not seeing", "Advice"]),
    "horseshoe": ("Horseshoe", ["Distant past", "Recent past", "Present", "Near future",
                                "External influences", "Advice", "Likely outcome"]),
    "cycle": ("Monthly Cycle", ["Seed (new moon)", "Action (first quarter)",
                                "Culmination (full moon)", "Release (last quarter)"]),
    "celtic": ("Celtic Cross", ["Present", "Challenge", "Conscious goal", "Foundation",
                                "Recent past", "Near future", "Self", "Environment",
                                "Hopes and fears", "Outcome"]),
}


def draw_spread(spread: str, seed: int) -> list:
    if spread not in SPREADS:
        raise ValueError(f"Unknown spread {spread!r}. Use {'|'.join(SPREADS)}.")
    rng = random.Random(seed)
    _name, positions = SPREADS[spread]
    cards = rng.sample(DECK, len(positions))
    return [{"position": pos, "card": card,
             "orientation": "reversed" if rng.random() < 0.5 else "upright"}
            for pos, card in zip(positions, cards)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Tarot draw (scripted randomness; seed always shown).")
    ap.add_argument("--spread", default="three", help="|".join(SPREADS))
    ap.add_argument("--seed", type=int, default=None, help="reproduce a previous draw")
    ap.add_argument("--question", default="", help="echoed in the output for the record")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    seed = args.seed if args.seed is not None else secrets.randbits(64)
    try:
        cards = draw_spread(args.spread, seed)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    spread_name = SPREADS[args.spread][0]
    if args.json:
        print(json.dumps({"spread": args.spread, "spread_name": spread_name,
                          "seed": seed, "question": args.question, "cards": cards},
                         ensure_ascii=False))
        return 0

    print(f"# {spread_name} — seed: {seed}")
    if args.question:
        print(f"Question: {args.question}")
    for r in cards:
        print(f"- {r['position']}: {r['card']} ({r['orientation']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
