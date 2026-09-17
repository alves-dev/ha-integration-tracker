#!/bin/sh
# Deploy this integration to the local Home Assistant test configuration.

set -eu

readonly INTEGRATION_DOMAIN="integration_tracker"
# Source component: custom_components/integration_tracker
readonly ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
readonly SOURCE_DIR="$ROOT_DIR/custom_components/$INTEGRATION_DOMAIN"
readonly HA_CONFIG_DIR="/home/alves-dev/projects/others/core/config"
readonly TARGET_DIR="$HA_CONFIG_DIR/custom_components/$INTEGRATION_DOMAIN"
readonly STOP_SCRIPT="$ROOT_DIR/dev/stop-ha.sh"
readonly START_SCRIPT="$ROOT_DIR/dev/start-ha.sh"

if [ ! -d "$SOURCE_DIR" ]; then
  echo "Integration source not found: $SOURCE_DIR" >&2
  exit 1
fi

if [ ! -d "$HA_CONFIG_DIR" ]; then
  echo "Home Assistant configuration directory was not found: $HA_CONFIG_DIR" >&2
  exit 1
fi

# Do not replace files while Home Assistant can load them.
sh "$STOP_SCRIPT"

mkdir -p "$(dirname -- "$TARGET_DIR")"
rm -rf "$TARGET_DIR"
cp -a "$SOURCE_DIR" "$TARGET_DIR"

echo "Copied $INTEGRATION_DOMAIN to $TARGET_DIR."
sh "$START_SCRIPT"
