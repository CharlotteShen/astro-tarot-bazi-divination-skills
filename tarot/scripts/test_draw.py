import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from draw import DECK, MAJORS, SPREADS, draw_spread, main  # noqa: E402


def test_deck_integrity():
    assert len(DECK) == 78
    assert len(set(DECK)) == 78
    assert len(MAJORS) == 22
    for suit in ("Wands", "Cups", "Swords", "Pentacles"):
        assert sum(1 for c in DECK if c.endswith(f"of {suit}")) == 14


def test_spread_counts():
    expected = {"single": 1, "three": 3, "relationship": 5, "decision": 5,
                "horseshoe": 7, "cycle": 4, "celtic": 10}
    assert {k: len(v[1]) for k, v in SPREADS.items()} == expected


def test_seed_reproducible():
    assert draw_spread("three", 42) == draw_spread("three", 42)
    assert draw_spread("three", 42) != draw_spread("three", 43)


def test_no_duplicates_and_valid_orientation():
    result = draw_spread("celtic", 7)
    cards = [r["card"] for r in result]
    assert len(set(cards)) == len(cards) == 10
    for r in result:
        assert set(r) == {"position", "card", "orientation"}
        assert r["orientation"] in ("upright", "reversed")
        assert r["card"] in DECK


def test_cli_prints_seed_and_question(capsys):
    rc = main(["--spread", "three", "--seed", "123", "--question", "test question?"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "seed: 123" in out and "test question?" in out
    assert out.count("(upright)") + out.count("(reversed)") == 3


def test_cli_json(capsys):
    rc = main(["--spread", "single", "--seed", "5", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["spread"] == "single" and data["seed"] == 5
    assert len(data["cards"]) == 1 and data["cards"][0]["card"] in DECK


def test_cli_unknown_spread_errors(capsys):
    rc = main(["--spread", "nope"])
    assert rc == 1
    assert "Error" in capsys.readouterr().err


MAJOR_ASTRO = {"Uranus", "Mercury", "Moon", "Venus", "Aries", "Taurus", "Gemini", "Cancer",
               "Leo", "Virgo", "Jupiter", "Libra", "Neptune", "Scorpio", "Sagittarius",
               "Capricorn", "Mars", "Aquarius", "Pisces", "Sun", "Pluto", "Saturn"}


def _card_rows():
    path = os.path.join(os.path.dirname(__file__), "..", "references", "cards.md")
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("|") and not line.startswith("|:") and "---" not in line \
                    and not line.startswith("| #"):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) == 8:
                    rows.append(cells)
    return rows


def test_cards_md_structure():
    rows = _card_rows()
    assert len(rows) == 78
    names = [r[1] for r in rows]
    assert len(set(names)) == 78
    majors = [r for r in rows if r[3] == "Major"]
    assert len(majors) == 22
    assert sorted(int(r[0]) for r in majors) == list(range(22))
    for suit in ("Wands", "Cups", "Swords", "Pentacles"):
        assert sum(1 for r in rows if r[3] == suit) == 14
    for r in rows:
        assert all(cell for cell in r), f"empty cell in {r[1]}"
        assert r[4] in ("Fire", "Water", "Air", "Earth")
        if r[3] == "Major":
            assert r[5] in MAJOR_ASTRO, f"bad astro for {r[1]}"
    deck_set = set(DECK)
    assert set(names) == deck_set   # names must exactly match draw.py's deck
