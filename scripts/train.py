"""Train an ACT policy on the B->A episodes via lerobot-train.

    uv run python scripts/train.py --config configs/act_b_to_a.yaml [--steps N] [--device cpu]
Extra unknown args are forwarded to lerobot-train.
"""
import argparse
import subprocess
import sys

import yaml

from common import episodes_for_task

ap = argparse.ArgumentParser()
ap.add_argument("--config", default="configs/act_b_to_a.yaml")
ap.add_argument("--steps", type=int)
ap.add_argument("--device")
ap.add_argument("--batch-size", type=int)
ap.add_argument("--output-dir")
args, extra = ap.parse_known_args()

c = yaml.safe_load(open(args.config))
for k in ("steps", "device", "batch_size", "output_dir"):
    if getattr(args, k) is not None:
        c[k] = getattr(args, k)

eps = episodes_for_task(c["dataset_root"], c["task"])
train_eps = eps[: -c["val_episodes"]] if c["val_episodes"] else eps
print(f"{len(eps)} episodes for task; training on {len(train_eps)}, holding out {len(eps) - len(train_eps)}")
a = c["act"]

cmd = [
    "lerobot-train",
    "--policy.type=act",
    "--policy.push_to_hub=false",
    f"--policy.device={c['device']}",
    f"--policy.chunk_size={a['chunk_size']}",
    f"--policy.n_action_steps={a['n_action_steps']}",
    f"--policy.vision_backbone={a['vision_backbone']}",
    f"--policy.kl_weight={a['kl_weight']}",
    f"--dataset.repo_id={c['dataset_repo_id']}",
    f"--dataset.root={c['dataset_root']}",
    f"--dataset.episodes={train_eps}",
    f"--dataset.image_transforms.enable={str(c['image_augmentation']).lower()}",
    f"--output_dir={c['output_dir']}",
    f"--steps={c['steps']}",
    f"--batch_size={c['batch_size']}",
    f"--num_workers={c['num_workers']}",
    f"--seed={c['seed']}",
    "--wandb.enable=false",
    *extra,
]
print(" ".join(cmd))
sys.exit(subprocess.call(cmd))
