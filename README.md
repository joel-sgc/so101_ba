# so101_ba — learn "move box B → A" on an SO-101

Imitation learning with **ACT** (Action Chunking Transformer, via [LeRobot](https://github.com/huggingface/lerobot)).
Inputs: front (top-down) camera + wrist camera + 6 joint positions. Output: 6 motor targets (chunk of 100 steps).

## Dataset
LeRobot v3.0 format, 30 fps, 53 episodes (45 B→A, 8 A→B), each ~20 s (move + return to home).
It lives in this folder (`data/ meta/ videos/`) and is **git-ignored**. Sync it from the server, e.g.
`rsync -av server:/path/to/dataset/{data,meta,videos} .`

## Why it tolerates a slightly-off box
- The box was placed *near* B (not exactly) in the demos, so the policy has to locate it from the images.
- Policy is closed-loop on both cameras (re-plans from what it sees, not a replayed trajectory).
- Image augmentation while training; ACT action chunks keep motion smooth.
- Check demos cover the range of box positions you expect at test time; add demos if not.

## Robot setup
Hardware ids, camera paths and `MJPG` settings mirror `scripts/record_route.sh` in
[joel-sgc/so101-abc-block-mover](https://github.com/joel-sgc/so101-abc-block-mover).
Calibration files `follower_calibration.json` / `leader_calibration.json` are committed here;
`scripts/install_calibration.sh` (run automatically by `run_robot.sh`) installs them as
`trevor_follower` / `trevor_leader`. Device paths are Pi-specific: override `FOLLOWER_PORT`, `FRONT`, `WRIST`
if the robot is plugged into a different machine.

## Use
```bash
uv sync
uv run python scripts/inspect_dataset.py          # sanity check
uv run python scripts/train.py --steps 2000 --device cpu   # smoke test
uv run python scripts/train.py                    # full run (needs a CUDA GPU, ~hours)
./scripts/run_robot.sh [checkpoint] # run on the robot (DEVICE=cpu if no GPU)
```
Config: [configs/act_b_to_a.yaml](configs/act_b_to_a.yaml). Last 4 B→A episodes are held out for validation.
