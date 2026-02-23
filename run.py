"""
run.py — Run a local LLM over a CSV file using Hugging Face pipelines.
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml
from tqdm import tqdm
from transformers import pipeline

from prompt import build_messages

# ─── Constants ────────────────────────────────────────────────────────────────

OUTPUTS_DIR = Path(__file__).parent / "outputs"
REQUIRED_COLUMNS = {"id", "text"}

# ─── Helpers ──────────────────────────────────────────────────────────────────


def load_config(path: Path) -> dict:
    """Load a YAML config file."""
    if not path.exists():
        raise FileNotFoundError(f"Config file not found at {path}")
    with path.open() as f:
        return yaml.safe_load(f)


def validate_csv(path: Path) -> pd.DataFrame:
    """
    Load and validate the input CSV. Raises an exception with a clear message
    if the file is missing or lacks the required columns — before any model
    loading occurs.
    """
    df = pd.read_csv(path)

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            "Input CSV is missing required column(s): "
            f"{', '.join(sorted(missing))}\n"
            f"Expected columns: '{', '.join(sorted(REQUIRED_COLUMNS))}'. "
            f"Found: {', '.join(df.columns.tolist())}"
        )

    if df.empty:
        raise ValueError("Input CSV has no rows.")

    return df


def print_sample_messages(messages: list[dict]) -> None:
    """Print a sample of messages."""
    for message in messages:
        print(f"<{message['role']}>\n{message['content']}\n\n")


def create_output_dir() -> Path:
    """Create a timestamped output directory and return its path."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = OUTPUTS_DIR / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


# ─── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        df = validate_csv(args.input)
        cfg = load_config(args.config)
    except (FileNotFoundError, ValueError) as e:
        sys.exit(f"Error: {e}")

    tqdm.pandas(desc="Building prompts")
    df["messages"] = df["text"].progress_apply(build_messages)

    if args.dry_run:
        print("\nDRY RUN — first prompt\n")
        print_sample_messages(df["messages"].iloc[0])
        return

    print("Loading pipeline...")
    pipe_kwargs = cfg.get("pipeline", {})
    if "num_workers" not in pipe_kwargs:
        pipe_kwargs["num_workers"] = os.cpu_count() or 1
    pipe = pipeline("text-generation", **pipe_kwargs)
    # Make sure tokenizer is set up correctly
    if pipe.tokenizer.pad_token is None:
        pipe.tokenizer.pad_token = pipe.tokenizer.eos_token
    pipe.tokenizer.padding_side = "left"

    # We pass messages as a generator so the pipeline yields outputs iteratively
    df["output"] = [
        output[0]["generated_text"]
        for output in tqdm(
            pipe((msg for msg in df["messages"]), **cfg.get("generation", {})),
            total=len(df),
            desc="Generating responses",
        )
    ]

    print("Saving outputs...")
    out_dir = create_output_dir()
    shutil.copy(args.config, out_dir / args.config.name)
    shutil.copy(Path(__file__).parent / "prompt.py", out_dir / "prompt.py")
    (out_dir / "cli_args.json").write_text(
        json.dumps({k: str(v) for k, v in vars(args).items()}, indent=4)
    )

    out_csv = out_dir / args.input.name
    out_json = out_csv.with_suffix(".json")

    df.to_csv(out_csv, index=False)
    df.to_json(out_json, orient="records", indent=4)

    print(f"Outputs saved to: {out_dir}")


if __name__ == "__main__":
    main()
