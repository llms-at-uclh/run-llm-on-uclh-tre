"""
run.py — Run a local LLM over a CSV file using vLLM offline batch inference.

Usage:
    python run.py --input data/myfile.csv --config config.yaml
    python run.py --input data/myfile.csv --config config.yaml --dry-run
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml
from tqdm import tqdm
from vllm import LLM, SamplingParams

from prompt import build_messages


# ─── Constants ────────────────────────────────────────────────────────────────

OUTPUTS_DIR = Path(__file__).parent / "outputs"
REQUIRED_COLUMNS = {"id", "text"}

# ─── Helpers ──────────────────────────────────────────────────────────────────


def load_config(path: Path) -> dict:
    """Load a YAML config file."""
    if not path.exists():
        sys.exit(f"Error: Config file not found at {path}")
    with path.open() as f:
        return yaml.safe_load(f)


def validate_csv(path: Path) -> pd.DataFrame:
    """
    Load and validate the input CSV. Exits immediately with a clear message
    if the file is missing or lacks the required columns — before any model
    loading occurs.
    """
    if not path.exists():
        sys.exit(f"Error: Input file not found: {path}")

    try:
        df = pd.read_csv(path)
    except Exception as e:
        sys.exit(f"Error: Could not read CSV file '{path}'.\nDetails: {e}")

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        sys.exit(
            f"Error: Input CSV is missing required column(s): {', '.join(sorted(missing))}\n"
            f"Expected columns: '{', '.join(sorted(REQUIRED_COLUMNS))}'. Found: {', '.join(df.columns.tolist())}"
        )

    if df.empty:
        sys.exit("Error: Input CSV has no rows.")

    return df


def create_output_dir() -> Path:
    """Create a timestamped output directory and return its path."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = OUTPUTS_DIR / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def format_conversation(conv: list[dict]) -> str:
    """Serialise a chat conversation to a human-readable string."""
    return "\n\n".join(f"[{m['role'].upper()}]\n{m['content']}" for m in conv)


def load_model(model_cfg: dict) -> LLM:
    """Load the vLLM model. Provides friendly error messages for common failures."""
    model_path = model_cfg.get("model")

    if not model_path:
        sys.exit("Error: 'model.model' is not set in config.yaml.")

    if not Path(model_path).exists():
        sys.exit(
            f"Error: Model directory not found: {model_path}\n"
            "Please check that 'model.model' in config.yaml points to the correct location."
        )

    print(f"Loading model from: {model_path}")
    print("This may take several minutes for large models...")

    try:
        llm = LLM(**model_cfg)
    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            sys.exit(
                "Error: GPU ran out of memory while loading the model.\n"
                "Try reducing 'model.gpu_memory_utilization' in config.yaml, "
                "or use a quantized model (set 'model.quantization' to e.g. 'awq')."
            )
        sys.exit(f"Error: Failed to load model.\nDetails: {e}")
    except Exception as e:
        sys.exit(f"Error: Failed to load model.\nDetails: {e}")

    return llm


# ─── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a local LLM over a CSV file using vLLM offline batch inference."
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help=f"Path to input CSV file (must have {sorted(REQUIRED_COLUMNS)} columns).",
    )
    parser.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Path to config YAML file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Format and print the first prompt, then exit without loading the model.",
    )
    args = parser.parse_args()

    # 1. Validate CSV immediately — before loading config or model.
    df = validate_csv(args.input)
    print(f"Input CSV loaded: {len(df)} rows")

    # 2. Load config.
    cfg = load_config(args.config)

    # 3. Build all message lists with a progress bar.
    print("Formatting prompts...")
    conversations = []
    for text in tqdm(df["text"].astype(str), unit="row"):
        conversations.append(build_messages(text))

    # 4. Dry-run: print the first prompt and exit.
    if args.dry_run:
        print("\n─── DRY RUN — first prompt ───────────────────────────────────────────────\n")
        print(format_conversation(conversations[0]))
        print("\n─────────────────────────────────────────────────────────────────────────")
        print("Dry run complete. No model was loaded. Exiting.")
        return

    # 5. Create output directory and copy config for audit trail.
    out_dir = create_output_dir()
    shutil.copy(args.config, out_dir / args.config.name)
    print(f"Output directory: {out_dir}")

    # 6. Load the model.
    sampling_params = SamplingParams(**cfg["sampling"])
    llm = load_model(cfg["model"])
    
    # 7. Run inference — vLLM applies the chat template internally via llm.chat().
    print(f"Running inference on {len(df)} rows...")
    try:
        outputs = llm.chat(
            messages=conversations,
            sampling_params=sampling_params,
            use_tqdm=True,
        )
    except Exception as e:
        sys.exit(f"Error: Inference failed.\nDetails: {e}")

    # 8. Extract generated text and write output CSV.
    df["prompt"] = [format_conversation(conv) for conv in conversations]
    df["output"] = [out.outputs[0].text.strip() for out in outputs]

    out_path = out_dir / args.input.name
    df[["id", "text", "prompt", "output"]].to_csv(out_path, index=False)

    print(f"\nDone. Results saved to: {out_path}")


if __name__ == "__main__":
    main()
