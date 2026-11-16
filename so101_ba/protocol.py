"""Wire protocol shared by pi_server, relay and run_policy.

Topology (every hop is plain ZMQ over TCP):

    Pi (robot+cams) --obs PUB--> Relay (laptop) --obs PUB--> Server (GPU, policy)
    Pi <--act PULL-- Relay <--act PUSH/PULL-- Server

Observation message (multipart):  [b"obs", header_json, jpeg_cam0, jpeg_cam1, ...]
Action message      (multipart):  [b"act", header_json]
header_json for obs: {"seq", "t", "state": [6], "cams": ["front", "wrist"]}
header_json for act: {"seq", "t", "action": [6], "obs_seq"}
Images are JPEGs of BGR frames (cv2.imencode); decode with decode_jpeg().
"""
import json
import time

import cv2
import numpy as np

JOINTS = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
CAMS = ["front", "wrist"]  # order matches dataset keys observation.images.<name>
OBS_PORT = 5555   # Pi publishes / relay republishes
ACT_PORT = 5556   # actions flow server -> relay -> Pi


def encode_jpeg(rgb: np.ndarray, quality: int = 85) -> bytes:
    ok, buf = cv2.imencode(".jpg", cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise RuntimeError("jpeg encode failed")
    return buf.tobytes()


def decode_jpeg(buf: bytes) -> np.ndarray:
    """-> HxWx3 uint8 RGB"""
    bgr = cv2.imdecode(np.frombuffer(buf, np.uint8), cv2.IMREAD_COLOR)
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def pack_obs(seq: int, state, frames: dict, quality: int = 85) -> list[bytes]:
    cams = list(frames)
    hdr = {"seq": seq, "t": time.time(), "state": [float(x) for x in state], "cams": cams}
    return [b"obs", json.dumps(hdr).encode(), *[encode_jpeg(frames[c], quality) for c in cams]]


def unpack_obs(parts: list[bytes]):
    assert parts[0] == b"obs", parts[0]
    hdr = json.loads(parts[1])
    frames = {c: decode_jpeg(b) for c, b in zip(hdr["cams"], parts[2:])}
    return hdr, np.asarray(hdr["state"], np.float32), frames


def pack_act(seq: int, action, obs_seq: int) -> list[bytes]:
    hdr = {"seq": seq, "t": time.time(), "action": [float(x) for x in action], "obs_seq": obs_seq}
    return [b"act", json.dumps(hdr).encode()]


def unpack_act(parts: list[bytes]):
    assert parts[0] == b"act", parts[0]
    hdr = json.loads(parts[1])
    return hdr, np.asarray(hdr["action"], np.float32)
