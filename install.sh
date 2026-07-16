#!/usr/bin/env bash
# install.sh — link the seven divination skills into your Claude Code skills folder.
#
# Usage:
#   ./install.sh              link all seven skills (symlinks; repo stays the source)
#   ./install.sh --copy       copy instead of symlink (repo can be deleted afterwards)
#   ./install.sh --uninstall  remove the seven symlinks
#
# Env: CLAUDE_SKILLS_DIR overrides the default ~/.claude/skills (used by tests).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
SKILLS=(natal-astrology tarot bazi ziwei xiuyao hecan astro-mbti)
MODE="link"
UNINSTALL=0

for arg in "$@"; do
  case "$arg" in
    --uninstall) UNINSTALL=1 ;;
    --copy) MODE="copy" ;;
    -h|--help) sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $arg (try --help)" >&2; exit 2 ;;
  esac
done

if [[ $UNINSTALL -eq 1 ]]; then
  for s in "${SKILLS[@]}"; do
    t="$SKILLS_DIR/$s"
    if [[ -L "$t" ]]; then rm "$t" && echo "removed  $t"
    elif [[ -d "$t" ]]; then echo "SKIPPED  $t is a real directory (not a symlink) — remove manually if intended."
    fi
  done
  echo "Uninstall done."
  exit 0
fi

mkdir -p "$SKILLS_DIR"
for s in "${SKILLS[@]}"; do
  src="$REPO_DIR/$s"; t="$SKILLS_DIR/$s"
  if [[ -L "$t" ]]; then rm "$t"
  elif [[ -e "$t" ]]; then
    echo "SKIPPED  $t already exists (earlier --copy install?). To update it: rm -rf \"$t\" then re-run." >&2
    continue
  fi
  if [[ "$MODE" == "copy" ]]; then cp -R "$src" "$t" && echo "copied  $s"
  else ln -s "$src" "$t" && echo "linked  $s"; fi
done

echo
if command -v python3 >/dev/null 2>&1; then
  ans=""; read -r -p "Install Python calculation engines now? (kerykeion, lunar-python, iztro-py) [y/N] " ans || true
  if [[ "$ans" =~ ^[Yy] ]]; then
    if ! python3 -m pip install \
      -r "$REPO_DIR/natal-astrology/scripts/requirements.txt" \
      -r "$REPO_DIR/bazi/scripts/requirements.txt" \
      -r "$REPO_DIR/ziwei/scripts/requirements.txt"; then
      echo
      echo "pip install failed — on Homebrew/Debian Python this is usually 'externally-managed-environment'."
      echo "No problem: the skills work without it (Route B — paste your chart from astro.com)."
      echo "To install the engines later, use a virtual environment:"
      echo "  python3 -m venv \"$REPO_DIR/.venv\""
      echo "  source \"$REPO_DIR/.venv/bin/activate\""
      echo "  pip install -r \"$REPO_DIR/natal-astrology/scripts/requirements.txt\" -r \"$REPO_DIR/bazi/scripts/requirements.txt\" -r \"$REPO_DIR/ziwei/scripts/requirements.txt\""
      echo "  then start Claude Code from that same shell (so python3 sees the packages)."
    fi
  else
    echo "Skipped — you can use Route B instead (paste your chart from astro.com; see docs/birth-data-setup.md)."
  fi
else
  echo "python3 not found — no problem: use Route B (paste your chart from astro.com; see docs/birth-data-setup.md)."
fi

if [[ "$MODE" == "copy" ]]; then BD="$SKILLS_DIR/natal-astrology/birth-data.md"
else BD="$REPO_DIR/natal-astrology/birth-data.md"; fi
if [[ ! -f "$BD" ]]; then
  ans=""; read -r -p "Create your private birth-data file from the template? [Y/n] " ans || true
  if [[ ! "$ans" =~ ^[Nn] ]]; then
    cp "$REPO_DIR/natal-astrology/birth-data.template.md" "$BD"
    echo "Created $BD — fill it in; it is gitignored and never leaves your machine."
  fi
fi

cat <<EOF

Done! Next steps:
  1. Fill in $BD   (guide: docs/birth-data-setup.md)
  2. Open a NEW Claude Code session
  3. Say:  "read my chart"  ·  「看看我的八字」  ·  "draw me a tarot card"
EOF
