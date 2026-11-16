#!/usr/bin/env bash
# On the GPU server: ./scripts/start_policy.sh <relay-ip> [extra run_policy args]
set -euo pipefail
cd "$(dirname "$0")/.."
exec uv run python scripts/run_policy.py --relay "${1:?relay ip/host}" "${@:2}"
