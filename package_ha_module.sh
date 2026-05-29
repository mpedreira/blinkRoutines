#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUT_DIR="$ROOT_DIR/dist"
STAMP="$(date +%Y%m%d_%H%M%S)"
ZIP_NAME="blink_routines_module_${STAMP}.zip"
ZIP_PATH="$OUT_DIR/$ZIP_NAME"

mkdir -p "$OUT_DIR"

cd "$ROOT_DIR/homeassistant/custom_components"
zip -r "$ZIP_PATH" blink_routines \
  -x "*/__pycache__/*" "*.pyc" "*.pyo" "*.DS_Store" > /dev/null

cp "$ZIP_PATH" "$ROOT_DIR/ha.zip"

echo "HA module zip created: $ZIP_PATH"
echo "Compatibility copy: $ROOT_DIR/ha.zip"
