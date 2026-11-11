"""Shared helpers: read episode metadata from the LeRobot v3 dataset."""
import glob
from pathlib import Path

import pandas as pd


def load_episodes(root: str | Path = ".") -> pd.DataFrame:
    files = sorted(glob.glob(str(Path(root) / "meta/episodes/chunk-*/*.parquet")))
    if not files:
        raise SystemExit(f"No episode metadata under {root}/meta/episodes")
    df = pd.concat([pd.read_parquet(f) for f in files]).sort_values("episode_index")
    df["task"] = df["tasks"].map(lambda t: t[0])
    return df.reset_index(drop=True)


def episodes_for_task(root, task: str) -> list[int]:
    df = load_episodes(root)
    return df.loc[df.task == task, "episode_index"].tolist()
