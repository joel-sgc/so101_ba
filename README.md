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
`scripts/install_calibration.sh` (run automatically by `start_pi.sh`) installs them as
`trevor_follower` / `trevor_leader`. Device paths are Pi-specific defaults in `scripts/pi_server.py`; override with `--port/--front/--wrist`.

## Architecture (ZMQ bridge)
```
 Pi (motors + cams)  <──TCP──>  your computer (relay)  <──TCP──>  GPU server (ACT policy)
 pi_server.py                   relay.py                         run_policy.py
```
- Pi → server: `obs` messages = joint state + JPEG front/wrist frames @ 30 Hz (PUB/SUB, newest wins).
- Server → Pi: `act` messages = 6 joint targets (PUSH/PULL). Pi applies only the newest, clamps
  per-step motion (`--max-step`, default 10°) and just holds position if actions stop (`--watchdog`).
- The relay forwards raw bytes in both directions; it connects to the Pi and the server connects to it.
- Wire format is in [so101_ba/protocol.py](so101_ba/protocol.py). Ports: 5555 (obs), 5556 (act) — open them
  between the machines. Use a LAN/VPN, the protocol has no auth.

## Use
Train (server, 5090):
```bash
uv sync
uv run python scripts/inspect_dataset.py
uv run python scripts/train.py            # configs/act_b_to_a.yaml
```
Run (start in this order; each machine: `git clone` + `uv sync`):
```bash
# 1. Pi        (installs calibration, owns robot+cameras)
./scripts/start_pi.sh
# 2. your computer
./scripts/start_relay.sh <pi-ip>
# 3. server — first verify the link (no GPU/policy; holds the arm still), then run the policy
uv run python scripts/bridge_check.py --relay <computer-ip> --save /tmp/frames
./scripts/start_policy.sh <computer-ip> --ckpt outputs/act_b_to_a/checkpoints/last/pretrained_model --episodes 5
```
Test without hardware: `uv run python scripts/mock_pi.py` instead of `start_pi.sh`.
Place the box near B before each episode; `--reset-s` gives you time between episodes.
Ctrl-C on the server stops commands; the arm holds its last pose.

Config: [configs/act_b_to_a.yaml](configs/act_b_to_a.yaml). Last 4 B→A episodes are held out for validation.
