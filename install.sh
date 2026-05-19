#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/FlipYourBits/codemonkeys.git"
BRANCH="main"

usage() {
  echo "Usage: $0 [--branch <branch>] [--dir <project-dir>]"
  echo ""
  echo "Install codemonkeys skills and agents into a project's .claude/ directory."
  echo ""
  echo "Options:"
  echo "  --branch <branch>   Git branch to install from (default: main)"
  echo "  --dir <path>        Target project directory (default: current directory)"
  echo "  --help              Show this help message"
  exit 0
}

target_dir="."
while [[ $# -gt 0 ]]; do
  case "$1" in
    --branch) BRANCH="$2"; shift 2 ;;
    --dir) target_dir="$2"; shift 2 ;;
    --help) usage ;;
    *) echo "Unknown option: $1"; usage ;;
  esac
done

target_dir="$(cd "$target_dir" && pwd)"

if ! command -v git &>/dev/null; then
  echo "Error: git is required but not installed."
  exit 1
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

echo "Fetching codemonkeys ($BRANCH)..."
git clone --depth 1 --branch "$BRANCH" "$REPO" "$tmp/codemonkeys" 2>/dev/null

src="$tmp/codemonkeys/.claude"
dest="$target_dir/.claude"

mkdir -p "$dest/agents" "$dest/skills" "$dest/shared"

echo "Installing agents..."
for agent in codemonkeys-code-reviewer codemonkeys-code-editor codemonkeys-researcher codemonkeys-test-reviewer; do
  rm -rf "$dest/agents/$agent"
  cp -r "$src/agents/$agent" "$dest/agents/"
done

echo "Installing skills..."
for skill in codemonkeys-bugfix codemonkeys-code-review codemonkeys-feature codemonkeys-research codemonkeys-smart-commit codemonkeys-test-quality codemonkeys-visualize; do
  rm -rf "$dest/skills/$skill"
  cp -r "$src/skills/$skill" "$dest/skills/"
done

echo "Installing shared guidelines..."
cp "$src/shared/"*.md "$dest/shared/"

echo ""
echo "Done. Installed to $dest/"
echo ""
echo "Available skills:"
echo "  /codemonkeys-code-review"
echo "  /codemonkeys-bugfix"
echo "  /codemonkeys-feature"
echo "  /codemonkeys-research"
echo "  /codemonkeys-visualize"
echo "  /codemonkeys-test-quality"
echo "  /codemonkeys-smart-commit"
