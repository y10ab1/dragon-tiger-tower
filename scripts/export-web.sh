#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
GODOT="${GODOT:-godot}"
mkdir -p "$ROOT/build/web"
"$GODOT" --headless --path "$ROOT/game" --import
"$GODOT" --headless --path "$ROOT/game" --export-release Web "$ROOT/build/web/index.html"
cp "$ROOT/game/assets/fonts/OFL.txt" "$ROOT/build/web/font-license.txt"
touch "$ROOT/build/web/.nojekyll"
