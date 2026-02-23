"""
run.py — Run a local LLM over a CSV file using Hugging Face pipelines.
"""

import argparse
import json
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from tqdm import tqdm
from transformers import pipeline

from prompt import build_messages

# ─── Constants ────────────────────────────────────────────────────────────────

OUTPUTS_DIR = Path(__file__).parent / "outputs"
REQUIRED_COLUMNS = {"id", "text"}

# ─── Global State ─────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)

# ─── Helpers ──────────────────────────────────────────────────────────────────


def setup_logging(output_dir: Path | None = None) -> None:
    """Set up logging to console and optionally to a file."""
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if output_dir:
        handlers.append(logging.FileHandler(output_dir / "run.log"))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )


def load_config(path: Path) -> dict[str, Any]:
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


def print_sample_messages(messages: list[dict[str, str]]) -> None:
    """Print a sample of messages using the logger."""
    for message in messages:
        logger.info("<%s>\n%s\n\n", message["role"], message["content"])


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

    # Create output dir early if not a dry run so we can log to it
    out_dir: Path | None = None
    if not args.dry_run:
        out_dir = create_output_dir()

    setup_logging(out_dir)

    try:
        df = validate_csv(args.input)
        cfg = load_config(args.config)
    except (FileNotFoundError, ValueError) as e:
        logger.error(e)
        sys.exit(1)

    tqdm.pandas(desc="Building prompts")
    df["messages"] = df["text"].progress_apply(build_messages)

    if args.dry_run:
        logger.info("DRY RUN — first prompt")
        print_sample_messages(df["messages"].iloc[0])
        return

    logger.info("Loading pipeline...")
    pipe_kwargs = cfg.get("pipeline", {})
    if "num_workers" not in pipe_kwargs:
        pipe_kwargs["num_workers"] = os.cpu_count() or 1
    if "trust_remote_code" not in pipe_kwargs:
        pipe_kwargs["trust_remote_code"] = False

    pipe = pipeline("text-generation", **pipe_kwargs)

    # Make sure tokenizer is set up correctly
    if pipe.tokenizer.pad_token is None:
        pipe.tokenizer.pad_token = pipe.tokenizer.eos_token
    pipe.tokenizer.padding_side = "left"

    logger.info("Starting generation...")
    # We pass messages as a generator so the pipeline yields outputs iteratively
    df["output"] = [
        output[0]["generated_text"]
        for output in tqdm(
            pipe((msg for msg in df["messages"]), **cfg.get("generation", {})),
            total=len(df),
            desc="Generating responses",
        )
    ]

    logger.info("Saving outputs...")
    # out_dir is guaranteed to be set if not args.dry_run
    assert out_dir is not None

    shutil.copy(args.config, out_dir / args.config.name)
    shutil.copy(Path(__file__).parent / "prompt.py", out_dir / "prompt.py")
    (out_dir / "cli_args.json").write_text(
        json.dumps({k: str(v) for k, v in vars(args).items()}, indent=4)
    )

    out_csv = out_dir / args.input.name
    out_json = out_csv.with_suffix(".json")

    df.to_csv(out_csv, index=False)
    df.to_json(out_json, orient="records", indent=4)

    logger.info("Outputs saved to: %s", out_dir)


if __name__ == "__main__":
    main()
