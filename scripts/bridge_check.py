"""Connectivity test from the server side (no policy/GPU needed): prints obs rate, state, latency
and echoes the current joint state back as a hold action (arm stays where it is).

    uv run python scripts/bridge_check.py --relay <laptop-ip> [--save frame_dir]
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cv2
import zmq

from so101_ba.protocol import ACT_PORT, OBS_PORT, pack_act, unpack_obs

ap = argparse.ArgumentParser()
ap.add_argument("--relay", required=True)
ap.add_argument("--obs-port", type=int, default=OBS_PORT)
ap.add_argument("--act-port", type=int, default=ACT_PORT)
ap.add_argument("--seconds", type=float, default=10)
ap.add_argument("--save", help="dir to write one frame per camera")
ap.add_argument("--no-hold", action="store_true", help="do not send hold actions")
a = ap.parse_args()

ctx = zmq.Context()
sub = ctx.socket(zmq.SUB); sub.setsockopt(zmq.SUBSCRIBE, b"obs"); sub.setsockopt(zmq.RCVHWM, 2)
sub.connect(f"tcp://{a.relay}:{a.obs_port}")
push = ctx.socket(zmq.PUSH); push.connect(f"tcp://{a.relay}:{a.act_port}")
n, t0, saved = 0, time.time(), False
while time.time() - t0 < a.seconds:
    if not sub.poll(2000):
        sys.exit("no observations received")
    hdr, state, frames = unpack_obs(sub.recv_multipart()); n += 1
    if not a.no_hold:
        push.send_multipart(pack_act(n, state, hdr["seq"]))
    if a.save and not saved:
        Path(a.save).mkdir(parents=True, exist_ok=True)
        for c, f in frames.items():
            cv2.imwrite(f"{a.save}/{c}.jpg", cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
        saved = True
    if n % 30 == 0:
        print(f"{n / (time.time() - t0):5.1f} Hz  age {1000 * (time.time() - hdr['t']):5.0f} ms (needs synced clocks)  state {state.round(1)}")
print("ok")
