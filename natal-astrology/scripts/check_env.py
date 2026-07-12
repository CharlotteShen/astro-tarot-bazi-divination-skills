"""One-time environment check for Route A (kerykeion chart generation)."""
import sys


def main() -> int:
    if sys.version_info < (3, 9):
        print(f"Python 3.9+ required; found {sys.version.split()[0]}.")
        return 1
    try:
        import kerykeion  # noqa: F401
    except ImportError:
        print("kerykeion is not installed. Install Route A dependencies with:")
        print("  pip install -r scripts/requirements.txt")
        print("Or skip Route A and paste chart data from astro.com (Route B).")
        return 1
    print("OK: Python and kerykeion are available. Route A is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
