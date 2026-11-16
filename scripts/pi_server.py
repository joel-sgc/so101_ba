"""Runs on the Raspberry Pi. Owns the motors + cameras.

Publishes observations (joint state + JPEG frames) and applies incoming actions.
Safety: per-step motion clamp (max_relative_target), joint-range clamp via calibration,
and a watchdog: if no action arrives for --watchdog seconds the arm just holds its last target.

    uv run python scripts/pi_server.py --obs-bind tcp://*:5555 --act-bind tcp://*:5556
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import time

import zmq

from so101_ba.protocol import ACT_PORT, JOINTS, OBS_PORT, pack_obs, unpack_act

try:  # lerobot >= 0.4 layout, fall back to older name
    from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
except ImportError:
    from lerobot.robots.so101_follower import SO101Follower, SO101FollowerConfig
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig

FOLLOWER_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B7A001171-if00"
FRONT = "/dev/v4l/by-id/usb-046d_Brio_101_2627APAAGJX8-video-index0"
WRIST = "/dev/v4l/by-id/usb-Generic_USB_HD_Camera_200910120001-video-index0"


def cam(path, w, h):
    return OpenCVCameraConfig(index_or_path=path, width=w, height=h, fps=30, fourcc="MJPG")


ap = argparse.ArgumentParser()
ap.add_argument("--obs-bind", default=f"tcp://*:{OBS_PORT}")
ap.add_argument("--act-bind", default=f"tcp://*:{ACT_PORT}")
ap.add_argument("--port", default=FOLLOWER_PORT)
ap.add_argument("--front", default=FRONT)
ap.add_argument("--wrist", default=WRIST)
ap.add_argument("--width", type=int, default=640)
ap.add_argument("--height", type=int, default=480)
ap.add_argument("--fps", type=float, default=30)
ap.add_argument("--jpeg-quality", type=int, default=85)
ap.add_argument("--max-step", type=float, default=10.0, help="max degrees a joint may move per command")
ap.add_argument("--watchdog", type=float, default=1.0)
a = ap.parse_args()

robot = SO101Follower(SO101FollowerConfig(
    id="trevor_follower", port=a.port, max_relative_target=a.max_step,
    cameras={"front": cam(a.front, a.width, a.height), "wrist": cam(a.wrist, a.width, a.height)},
))
robot.connect()  # uses calibration trevor_follower.json (scripts/install_calibration.sh)

ctx = zmq.Context()
pub = ctx.socket(zmq.PUB); pub.setsockopt(zmq.SNDHWM, 2); pub.bind(a.obs_bind)
pull = ctx.socket(zmq.PULL); pull.setsockopt(zmq.RCVHWM, 4); pull.bind(a.act_bind)

print(f"pi_server up: obs {a.obs_bind}, act {a.act_bind}")
period, seq, last_act, n_act, warned = 1 / a.fps, 0, time.time(), 0, False
try:
    while True:
        t0 = time.perf_counter()
        obs = robot.get_observation()
        state = [obs[f"{j}.pos"] for j in JOINTS]
        pub.send_multipart(pack_obs(seq, state, {c: obs[c] for c in ("front", "wrist")}, a.jpeg_quality), copy=False)
        seq += 1

        # drain to the newest queued action only (stale actions are useless)
        newest = None
        while pull.poll(0):
            newest = pull.recv_multipart()
        if newest is not None:
            _, act = unpack_act(newest)
            robot.send_action({f"{j}.pos": float(v) for j, v in zip(JOINTS, act)})
            last_act, n_act, warned = time.time(), n_act + 1, False
        elif n_act and not warned and time.time() - last_act > a.watchdog:
            print("watchdog: no actions, holding position")
            warned = True

        time.sleep(max(0.0, period - (time.perf_counter() - t0)))
except KeyboardInterrupt:
    pass
finally:
    robot.disconnect()
