#!/usr/bin/env bash
# Run a trained policy on the real SO-101 (closed loop on both cameras + joint state).
# Usage: PORT=/dev/ttyACM0 FRONT=0 WRIST=2 ./scripts/run_robot.sh [checkpoint_dir]
set -euo pipefail
CKPT="${1:-outputs/act_b_to_a/checkpoints/last/pretrained_model}"
PORT="${PORT:?set PORT, e.g. /dev/ttyACM0}"
FRONT="${FRONT:-0}"; WRIST="${WRIST:-2}"
ROBOT_ID="${ROBOT_ID:-my_follower}"   # must match the calibration used when recording
exec uv run lerobot-record \
  --robot.type=so101_follower --robot.port="$PORT" --robot.id="$ROBOT_ID" \
  --robot.cameras="{ front: {type: opencv, index_or_path: $FRONT, width: 640, height: 480, fps: 30}, wrist: {type: opencv, index_or_path: $WRIST, width: 640, height: 480, fps: 30} }" \
  --display_data=true \
  --dataset.repo_id="local/eval_so101_ba_$(date +%s)" \
  --dataset.single_task="Move the block from spot B to spot A" \
  --dataset.episode_time_s=20 --dataset.num_episodes=5 --dataset.push_to_hub=false \
  --policy.path="$CKPT"
