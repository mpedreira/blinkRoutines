#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Generating deployment bundles..."
"$ROOT_DIR/package_ha_module.sh"
"$ROOT_DIR/package_ha_local.sh"
"$ROOT_DIR/package_docker_bundle.sh"

echo ""
echo "Done. Generated files:"
ls -lh "$ROOT_DIR"/ha.zip "$ROOT_DIR"/ha_local.zip "$ROOT_DIR"/docker_bundle.zip
