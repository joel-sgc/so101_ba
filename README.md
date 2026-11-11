# so101_ba — learn "move box B → A" on an SO-101

Imitation learning with **ACT** (Action Chunking Transformer, via [LeRobot](https://github.com/huggingface/lerobot)).
Inputs: front (top-down) camera + wrist camera + 6 joint positions. Output: 6 motor targets (chunk of 100 steps).

## Dataset
LeRobot v3.0 format, 30 fps, 53 episodes (45 B→A, 8 A→B), each ~20 s (move + return to home).
It lives in this folder (`data/ meta/ videos/`) and is **git-ignored**. Sync it from the server, e.g.
`rsync -av server:/path/to/dataset/{data,meta,videos} .`

## Why it tolerates a slightly-off box
- Policy is closed-loop on both cameras (it re-plans from what it sees, not a replayed trajectory).
- Image augmentation (crop/color jitter) while training; ACT's action chunks keep motion smooth.
- Demos should vary the box position a little — if all 45 demos have the box in the exact same spot,
  expect poor generalisation. Record ~20 extra demos with box shifted ±2–3 cm / rotated if needed.

## Use
```bash
uv sync
uv run python scripts/inspect_dataset.py          # sanity check
uv run python scripts/train.py --steps 2000 --device cpu   # smoke test
uv run python scripts/train.py                    # full run (needs a CUDA GPU, ~hours)
PORT=/dev/ttyACM0 FRONT=0 WRIST=2 ./scripts/run_robot.sh  # run on the robot
```
Config: [configs/act_b_to_a.yaml](configs/act_b_to_a.yaml). Last 4 B→A episodes are held out for validation.
Camera indexes / robot id must match how the data was recorded.
