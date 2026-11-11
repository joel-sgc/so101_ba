#!/usr/bin/env bash
# Run a trained policy on the real SO-101 (closed loop on both cameras + joint state).
# Same robot/camera settings as record_route.sh in joel-sgc/so101-abc-block-mover.
# Usage: ./scripts/run_robot.sh [checkpoint_dir] [num_episodes] [episode_s]
# Override device paths via env if the machine differs (FOLLOWER_PORT, FRONT, WRIST).
set -euo pipefail
cd "$(dirname "$0")/.."
./scripts/install_calibration.sh >/dev/null
CKPT=${1:-outputs/act_b_to_a/checkpoints/last/pretrained_model}
N=${2:-5}; EP=${3:-20}
FOLLOWER_PORT=${FOLLOWER_PORT:-/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B7A001171-if00}
FRONT=${FRONT:-/dev/v4l/by-id/usb-046d_Brio_101_2627APAAGJX8-video-index0}
WRIST=${WRIST:-/dev/v4l/by-id/usb-Generic_USB_HD_Camera_200910120001-video-index0}
CAM="{front: {type: opencv, index_or_path: $FRONT, width: 640, height: 480, fps: 30, fourcc: MJPG}, wrist: {type: opencv, index_or_path: $WRIST, width: 640, height: 480, fps: 30, fourcc: MJPG}}"
exec uv run lerobot-record \
  --robot.type=so101_follower --robot.id=trevor_follower \
  --robot.port="$FOLLOWER_PORT" --robot.cameras="$CAM" \
  --dataset.repo_id="local/eval_so101_ba" --dataset.root="outputs/eval_$(date +%s)" \
  --dataset.single_task="Move the block from spot B to spot A" \
  --dataset.num_episodes="$N" --dataset.episode_time_s="$EP" --dataset.reset_time_s=10 \
  --dataset.push_to_hub=false --play_sounds=false \
  --policy.path="$CKPT" --policy.device="${DEVICE:-cuda}"
