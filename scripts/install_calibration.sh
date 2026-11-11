#!/usr/bin/env bash
# Copy the calibration files shipped in this repo to where LeRobot looks for them.
# ids must match the recording setup: trevor_follower / trevor_leader.
set -euo pipefail
cd "$(dirname "$0")/.."
C="${HF_HOME:-$HOME/.cache/huggingface}/lerobot/calibration"
mkdir -p "$C/robots/so_follower" "$C/teleoperators/so_leader"
cp follower_calibration.json "$C/robots/so_follower/trevor_follower.json"
cp leader_calibration.json   "$C/teleoperators/so_leader/trevor_leader.json"
echo "installed to $C"
