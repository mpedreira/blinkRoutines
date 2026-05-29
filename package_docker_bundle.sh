#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUT_DIR="$ROOT_DIR/dist"
STAMP="$(date +%Y%m%d_%H%M%S)"
ZIP_NAME="blink_docker_bundle_${STAMP}.zip"
ZIP_PATH="$OUT_DIR/$ZIP_NAME"

mkdir -p "$OUT_DIR"

INCLUDE_PATHS=(
  "agents"
  "app"
  "config"
  "requirements.txt"
  "requirements-dev.txt"
  "README.md"
)

EXISTING_PATHS=()
for p in "${INCLUDE_PATHS[@]}"; do
  if [[ -e "$ROOT_DIR/$p" ]]; then
    EXISTING_PATHS+=("$p")
  fi
done

if [[ ${#EXISTING_PATHS[@]} -eq 0 ]]; then
  echo "No files found to package for docker bundle"
  exit 1
fi

cd "$ROOT_DIR"
zip -r "$ZIP_PATH" "${EXISTING_PATHS[@]}" \
  -x "*/__pycache__/*" "*.pyc" "*.pyo" "*.DS_Store" ".git/*" ".venv/*" "agents/data/*" > /dev/null

cp "$ZIP_PATH" "$ROOT_DIR/docker_bundle.zip"

echo "Docker bundle zip created: $ZIP_PATH"
echo "Compatibility copy: $ROOT_DIR/docker_bundle.zip"
