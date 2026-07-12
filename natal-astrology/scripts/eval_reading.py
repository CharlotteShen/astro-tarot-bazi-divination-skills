"""Reading-quality eval grader: checks a generated reading against an authored expectation file.
Deterministic (pure regex over text) — no ephemeris, no network. Catches fabrication (forbidden),
missed headlines (must_mention), and dropped reliability flags (must_flag). Verdicts are advisory:
a FAIL means "inspect" — a grounded paraphrase may defeat a pattern; fix the pattern, not the reading.
"""
import argparse
import json
import re
import sys


def grade(expect: dict, reading_text: str) -> dict:
    results = []

    def check(items, kind, want_match):
        for item in items or []:
            matched = None
            for pat in item.get("patterns", []):
                if re.search(pat, reading_text):
                    matched = pat
                    break
            ok = (matched is not None) if want_match else (matched is None)
            results.append({"kind": kind, "desc": item.get("desc", ""),
                            "ok": ok, "matched_pattern": matched})

    check(expect.get("must_mention"), "must_mention", True)
    check(expect.get("forbidden"), "forbidden", False)
    check(expect.get("must_flag"), "must_flag", True)

    passed = all(r["ok"] for r in results)
    counts = {"total": len(results),
              "passed": sum(1 for r in results if r["ok"]),
              "failed": sum(1 for r in results if not r["ok"])}
    return {"passed": passed, "results": results, "counts": counts}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Grade a reading against an expectation file.")
    ap.add_argument("--expect", required=True, help="expectation JSON file")
    ap.add_argument("--reading", required=True, help="reading markdown/text file")
    args = ap.parse_args(argv)

    try:
        with open(args.expect, encoding="utf-8") as f:
            expect = json.load(f)
        with open(args.reading, encoding="utf-8") as f:
            reading = f.read()
    except Exception as e:  # noqa: BLE001 — clean message, no traceback
        print(f"Error: {e}", file=sys.stderr)
        return 1

    r = grade(expect, reading)
    for item in r["results"]:
        print(f"[{'PASS' if item['ok'] else 'FAIL'}] {item['kind']}: {item['desc']}")
    c = r["counts"]
    print(f"\n{c['passed']}/{c['total']} checks passed — {'PASS' if r['passed'] else 'FAIL'}")
    return 0 if r["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
