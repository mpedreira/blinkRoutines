#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUT_DIR="$ROOT_DIR/dist"
STAMP="$(date +%Y%m%d_%H%M%S)"
ZIP_NAME="ha_local_${STAMP}.zip"
ZIP_PATH="$OUT_DIR/$ZIP_NAME"

mkdir -p "$OUT_DIR"

# Build an archive that matches server-side extraction flow under /root/homeassistant.
STAGE_DIR="$ROOT_DIR/.tmp_ha_local"
rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR/root/homeassistant/custom_components"
cp -R "$ROOT_DIR/homeassistant/custom_components/blink_routines" "$STAGE_DIR/root/homeassistant/custom_components/"

find "$STAGE_DIR" -type d -name "__pycache__" -prune -exec rm -rf {} +
find "$STAGE_DIR" -type f \( -name "*.pyc" -o -name "*.pyo" -o -name ".DS_Store" \) -delete

cd "$STAGE_DIR"
zip -r "$ZIP_PATH" root > /dev/null

cp "$ZIP_PATH" "$ROOT_DIR/ha_local.zip"
rm -rf "$STAGE_DIR"

echo "HA local zip created: $ZIP_PATH"
echo "Compatibility copy: $ROOT_DIR/ha_local.zip"
