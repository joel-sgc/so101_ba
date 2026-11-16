#!/usr/bin/env bash
# On your computer: ./scripts/start_relay.sh <pi-ip>
set -euo pipefail
cd "$(dirname "$0")/.."
exec uv run python scripts/relay.py --pi "${1:?pi ip/host}" "${@:2}"
