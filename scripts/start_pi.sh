#!/usr/bin/env bash
# On the Pi: ./scripts/start_pi.sh
set -euo pipefail
cd "$(dirname "$0")/.."
./scripts/install_calibration.sh
exec uv run python scripts/pi_server.py "$@"
