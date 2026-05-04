#!/bin/bash
set -e

echo "=== Building Lambda deployment packages ==="

# ── Layer (dependencies) ─────────────────────────────────────────────────────
echo "[1/2] Building layer.zip..."
rm -rf python layer.zip
mkdir python
pip install -r requirements.txt -t python/ --quiet \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.14 \
    --only-binary=:all:
zip -r9 layer.zip python/ > /dev/null
rm -rf python
echo "      layer.zip ready ($(du -sh layer.zip | cut -f1))"

# ── App code ─────────────────────────────────────────────────────────────────
cp config/config.ini config/config_local.ini 2>/dev/null || true
cp config/config_aws.ini config/config.ini 2>/dev/null || true
echo "[2/2] Building app.zip..."
if [[ ! -f config/config.ini ]]; then
  echo "WARNING: config/config.ini not found – Lambda will start with empty config (re-auth required)"
fi
cp config/config.ini config/config_local.ini 2>/dev/null || true

rm -f app.zip
zip -r9 app.zip app/ config/ > /dev/null
echo "      app.zip ready ($(du -sh app.zip | cut -f1))"

echo ""
echo "Deploy:"
echo "  1. Upload layer.zip  → Lambda > Layers > Create/update layer (Python 3.x)"
echo "  2. Upload app.zip    → Lambda > Function > Upload from .zip file"
echo "  3. Set handler       → app.main.handler"
