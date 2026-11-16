"""Runs on your computer (the middle man). Forwards bytes both ways, never decodes images.

    Pi  --obs-->  [SUB connect]  relay  [PUB bind]  --obs-->  Server
    Pi  <--act--  [PUSH connect] relay  [PULL bind] <--act--  Server

    uv run python scripts/relay.py --pi 192.168.1.50
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import time

import zmq

from so101_ba.protocol import ACT_PORT, OBS_PORT

ap = argparse.ArgumentParser()
ap.add_argument("--pi", required=True, help="Pi host/IP")
ap.add_argument("--obs-port", type=int, default=OBS_PORT)
ap.add_argument("--act-port", type=int, default=ACT_PORT)
ap.add_argument("--listen", default="*", help="interface the server connects to")
ap.add_argument("--listen-obs-port", type=int, help="default: --obs-port")
ap.add_argument("--listen-act-port", type=int, help="default: --act-port")
a = ap.parse_args()

ctx = zmq.Context()
sub = ctx.socket(zmq.SUB); sub.setsockopt(zmq.SUBSCRIBE, b"obs"); sub.setsockopt(zmq.RCVHWM, 2)
sub.connect(f"tcp://{a.pi}:{a.obs_port}")
pub = ctx.socket(zmq.PUB); pub.setsockopt(zmq.SNDHWM, 2)
pub.bind(f"tcp://{a.listen}:{a.listen_obs_port or a.obs_port}")
pull = ctx.socket(zmq.PULL); pull.setsockopt(zmq.RCVHWM, 4)
pull.bind(f"tcp://{a.listen}:{a.listen_act_port or a.act_port}")
push = ctx.socket(zmq.PUSH); push.setsockopt(zmq.SNDHWM, 4)
push.connect(f"tcp://{a.pi}:{a.act_port}")

poller = zmq.Poller(); poller.register(sub, zmq.POLLIN); poller.register(pull, zmq.POLLIN)
n_obs = n_act = 0; t_rep = time.time()
print(f"relay up: pi={a.pi}; server connects to {a.listen}:{a.listen_obs_port or a.obs_port} (obs) / {a.listen_act_port or a.act_port} (act)")
try:
    while True:
        ev = dict(poller.poll(1000))
        if sub in ev:
            pub.send_multipart(sub.recv_multipart(), copy=False); n_obs += 1
        if pull in ev:
            try:
                push.send_multipart(pull.recv_multipart(), flags=zmq.NOBLOCK); n_act += 1
            except zmq.Again:
                pass  # Pi unreachable: drop rather than queue stale actions
        if time.time() - t_rep > 5:
            print(f"obs fwd {n_obs / 5:.1f}/s  act fwd {n_act / 5:.1f}/s"); n_obs = n_act = 0; t_rep = time.time()
except KeyboardInterrupt:
    pass
