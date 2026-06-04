#!/bin/bash
# Install paper-intensive-reading skill to project-level skills directories.
# Run from project root.
#
# Usage:
#   ./scripts/install-skill.sh
#
# This creates:
#   .opencode/skills/paper-intensive-reading/   (for opencode)
#   .claude/skills/paper-intensive-reading/     (for Claude Code)
#
# Each copy has its own venv (no global Python install).
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

FILES_TO_COPY=(
  "SKILL.md"
  "pyproject.toml"
  "README.md"
  "paper_intensive_reading"
  "references"
)

for SUBDIR in ".opencode/skills" ".claude/skills"; do
  DEST="$PROJECT_ROOT/$SUBDIR/paper-intensive-reading"
  echo "→ Installing to $DEST"
  mkdir -p "$DEST"

  for f in "${FILES_TO_COPY[@]}"; do
    if [ -e "$PROJECT_ROOT/$f" ]; then
      cp -R "$PROJECT_ROOT/$f" "$DEST/"
    else
      echo "  ! WARNING: $f not found in project root, skipping"
    fi
  done

  echo "  → Running uv sync (this may take a minute)..."
  (cd "$DEST" && uv sync)
  echo "  ✓ Done"
  echo
done

echo "✓ Skill installed. Both opencode and Claude Code can now use it."
echo "  Triggers: /paper-read, /paper-list, /paper-survey"
