"""Runs on the GPU server. Closed-loop ACT inference over the ZMQ bridge.

    uv run python scripts/run_policy.py --relay <laptop-ip> --ckpt outputs/act_b_to_a/checkpoints/last/pretrained_model
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import time

import numpy as np
import torch
import zmq

from so101_ba.protocol import ACT_PORT, CAMS, OBS_PORT, pack_act, unpack_obs

ap = argparse.ArgumentParser()
ap.add_argument("--relay", required=True, help="host/IP of the relay (your computer)")
ap.add_argument("--ckpt", default="outputs/act_b_to_a/checkpoints/last/pretrained_model")
ap.add_argument("--obs-port", type=int, default=OBS_PORT)
ap.add_argument("--act-port", type=int, default=ACT_PORT)
ap.add_argument("--fps", type=float, default=30)
ap.add_argument("--episode-s", type=float, default=20)
ap.add_argument("--episodes", type=int, default=1)
ap.add_argument("--reset-s", type=float, default=10, help="pause between episodes to reposition the box")
ap.add_argument("--device", default="cuda")
a = ap.parse_args()

from lerobot.policies.act.modeling_act import ACTPolicy
from lerobot.policies.factory import make_pre_post_processors

policy = ACTPolicy.from_pretrained(a.ckpt).to(a.device).eval()
pre, post = make_pre_post_processors(policy.config, a.ckpt, preprocessor_overrides={"device_processor": {"device": a.device}})

ctx = zmq.Context()
sub = ctx.socket(zmq.SUB); sub.setsockopt(zmq.SUBSCRIBE, b"obs"); sub.setsockopt(zmq.RCVHWM, 2)  # CONFLATE does not support multipart
sub.connect(f"tcp://{a.relay}:{a.obs_port}")
push = ctx.socket(zmq.PUSH); push.setsockopt(zmq.SNDHWM, 2); push.connect(f"tcp://{a.relay}:{a.act_port}")


def latest_obs(timeout_ms=2000):
    if not sub.poll(timeout_ms):
        raise TimeoutError("no observation from bridge (are pi_server and relay running?)")
    parts = sub.recv_multipart()
    while sub.poll(0):  # drop stale frames, keep newest
        parts = sub.recv_multipart()
    return unpack_obs(parts)


def to_batch(state, frames):
    b = {"observation.state": torch.from_numpy(state)[None]}
    for c in CAMS:
        b[f"observation.images.{c}"] = torch.from_numpy(frames[c]).permute(2, 0, 1).float().div(255)[None]
    return b


period, seq = 1 / a.fps, 0
print("waiting for first observation..."); latest_obs(10000); print("connected")
try:
    for ep in range(a.episodes):
        policy.reset(); pre.reset(); post.reset()
        print(f"episode {ep + 1}/{a.episodes}")
        t_end = time.perf_counter() + a.episode_s
        while time.perf_counter() < t_end:
            t0 = time.perf_counter()
            hdr, state, frames = latest_obs()
            with torch.inference_mode():
                act = post(policy.select_action(pre(to_batch(state, frames))))
            push.send_multipart(pack_act(seq, act.squeeze(0).float().cpu().numpy(), hdr["seq"]))
            seq += 1
            time.sleep(max(0.0, period - (time.perf_counter() - t0)))
        if ep + 1 < a.episodes:
            print(f"reset: reposition the box ({a.reset_s}s)"); time.sleep(a.reset_s)
except KeyboardInterrupt:
    pass
print("done")
