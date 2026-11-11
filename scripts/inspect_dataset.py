"""Print a summary of the dataset: tasks, episode counts, lengths."""
import sys
from common import load_episodes

df = load_episodes(sys.argv[1] if len(sys.argv) > 1 else ".")
print(df.groupby("task").length.agg(["count", "mean", "min", "max"]))
print("total frames:", df.length.sum())
