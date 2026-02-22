# Run LLM on UCLH TRE

Run a local large language model (LLM) over a CSV of clinical text using [vLLM](https://docs.vllm.ai/) offline batch inference. Designed for use in the Azure Trusted Research Environment (TRE) where there is no internet access.

---

## Repository layout

```
run-llm-on-uclh-tre/
├── config_tre.yaml       ← TRE config (GPU, full model path)
├── config_local.yaml     ← Local laptop config (CPU, tiny model)
├── prompt.py             ← Edit this: what you want the model to do
├── run.py                ← Main script (do not edit unless you know what you're doing!)
├── requirements.txt      ← Python dependencies
├── data/
│   └── example_input.csv ← Example input file
└── outputs/              ← Created automatically when you run the script
    └── 2025-01-15_10-30-00/
        ├── example_input.csv  ← Results (id, text, prompt, output columns)
        └── config.yaml        ← Copy of config used (audit trail)
```

---

## Step 1: Install dependencies

Open a terminal in the repository folder and run:

```bash
python -m venv .venv
source .venv/bin/activate       # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> **TRE users:** packages are installed from the internal Nexus mirror. If a package is missing, contact your TRE administrator to request it.

---

## Step 2: Download a model

**Testing locally on your laptop (no GPU required)**

A tiny model is provided for verifying your prompt works before using the TRE.
It runs on CPU so is slow, but good enough for checking outputs look correct.

```bash
pip install huggingface-hub
huggingface-cli download Qwen/Qwen3-0.6B --local-dir ./models/Qwen3-0.6B
```

This saves the model to `./models/Qwen3-0.6B`. The `config_local.yaml` file already points here — no further config changes needed.

**In the TRE**

The route is to download the model from Hugging Face and then upload it to the airlock for approval and then download it to your virtual machine.

- First look in the airlock to see if the model is already there
- If not, download it from Hugging Face, zip the folder
```bash
huggingface-cli download <HUGGING_FACE_MODEL> --local-dir ./models/<MODEL_NAME>
zip -r ./models/<MODEL_NAME>.zip ./models/<MODEL_NAME>
```
- Then upload/download to the airlock as documented in the [SAFEHR docs](https://github.com/SAFEHR-data/safehr-data-service-catalogue/blob/main/User-Guides/TRE/import-data-to-the-TRE-workspace.md#import-data-to-the-tre-workspace)

---

## Step 3: Edit `config.yaml`

Open `config.yaml` and set `model.model` to the path of your model directory:

```yaml
model:
  model: /path/to/your/model   # ← change this
```

Update any other parameters as needed. Full parameter references are linked in the config file itself.

---

## Step 4: Edit `prompt.py`

Open `prompt.py` and edit:

1. **`SYSTEM_PROMPT`** — the model's overall role and instructions
2. **The user message in `build_messages()`** — what you want done with each row

Use `{text}` where you want the row's content inserted:

```python
{"role": "user", "content": f"Summarise the following:\n\n{text}"}
```

> **Tip:** use `--dry-run` to preview your prompt before a full run (see below).

---

## Step 5: Prepare your input CSV

Your input file must have exactly these two columns:

| `id` | `text` |
|---|---|
| 1 | Patient is a 67-year-old... |
| 2 | 72-year-old female admitted... |

An example file is at `data/example_input.csv`.

---

## Step 6: Run

**Preview your prompt first (recommended):**

```bash
# Local laptop (CPU, tiny model):
python run.py --input data/example_input.csv --config config/cpu.yaml --dry-run

# TRE (GPU, full model):
python run.py --input data/example_input.csv --config config/gpu.yaml --dry-run
```

This prints the first formatted prompt without loading the model.

**Run the full job:**

```bash
# Local laptop:
python run.py --input data/example_input.csv --config config/cpu.yaml

# TRE:
python run.py --input data/example_input.csv --config config/gpu.yaml
```

> Inference on CPU with the 0.5B model takes roughly 1–2 minutes for a small CSV — enough to confirm outputs look right.

---

## Outputs

Results are saved to `outputs/<timestamp>/`. This folder contains:

- **`<your_filename>.csv`** — your original data with two added columns:
  - **`prompt`** — the full formatted prompt sent to the model for that row
  - **`output`** — the model's response
- **`config[_local].yaml`** — exact copy of the config used (audit trail)

---

## Supported quantised models

Set `model.quantization` in `config.yaml` to one of: `"awq"`, `"gptq"`, `"fp8"`, `"squeezellm"`, or `null` for full precision.

---

## Troubleshooting

**Out of memory**
> Reduce `model.gpu_memory_utilization` (e.g. `0.7`) or use a quantized model.

**"Model directory not found"**
> Check `model.model` in `config.yaml` is the correct absolute path.

**"Input CSV is missing required column(s)"**
> Column names must be exactly `id` and `text` (lowercase).
