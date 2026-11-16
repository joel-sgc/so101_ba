"""Hardware-free stand-in for pi_server.py (for testing relay + run_policy on any machine).
Publishes synthetic frames and a fake joint state that follows received actions."""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import zmq

from so101_ba.protocol import ACT_PORT, OBS_PORT, pack_obs, unpack_act

ap = argparse.ArgumentParser()
ap.add_argument("--obs-bind", default=f"tcp://*:{OBS_PORT}")
ap.add_argument("--act-bind", default=f"tcp://*:{ACT_PORT}")
ap.add_argument("--fps", type=float, default=30)
a = ap.parse_args()

ctx = zmq.Context()
pub = ctx.socket(zmq.PUB); pub.bind(a.obs_bind)
pull = ctx.socket(zmq.PULL); pull.bind(a.act_bind)
state = np.zeros(6, np.float32); seq = 0; n_act = 0
print("mock_pi up")
while True:
    t0 = time.perf_counter()
    img = np.random.randint(0, 255, (480, 640, 3), np.uint8)
    pub.send_multipart(pack_obs(seq, state, {"front": img, "wrist": img})); seq += 1
    while pull.poll(0):
        hdr, act = unpack_act(pull.recv_multipart()); state = act; n_act += 1
        if n_act % 30 == 0:
            print(f"got {n_act} actions, latest {np.round(act, 1)}")
    time.sleep(max(0, 1 / a.fps - (time.perf_counter() - t0)))
