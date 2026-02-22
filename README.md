# Run LLM on UCLH TRE

Run a local large language model (LLM) over a CSV of clinical text using [vLLM](https://docs.vllm.ai/) offline batch inference. Designed for use in the Azure Trusted Research Environment (TRE) directly on the virtual machine (not via Azure ML).

### Non-computer scientists

There are two main "levers" to control via this setup
1. The prompt in `prompt.py`
2. The model and sampling parameters in `config.yaml`

Initally, it is highly recommend to 
1. Get familiar with the codebase by installing and running it locally on your laptop, using the `--dry-run` flag [here](#step-6-run). This will print the first prompt to the console without loading the model allowing for easy debugging and prompt iteration.
2. Read the vLLM docs for [LLMs](https://docs.vllm.ai/en/latest/api/vllm/#vllm.LLM) and [SamplingParams](https://docs.vllm.ai/en/latest/api/vllm/#vllm.SamplingParams)
3. Then follow the steps below to run it in the TRE

### Computer scientists

This is a very simple setup to run a local LLM over a CSV file using vLLM offline batch inference. It is designed for use in the Azure Trusted Research Environment (TRE) where there is no internet access.

vLLM can do much more than this, please use this as a starting point and build upon and share!!

---

## Repository layout

```
run-llm-on-uclh-tre/
├── config.yaml           ← Model configuration (model path, parameters)
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

> TRE Packages are installed from the internal Nexus mirror. If a package is missing, contact your TRE administrator to request it.

---

## Step 2: Download a model

**In the TRE**

The route is to download the model from Hugging Face and then upload it to the airlock for approval and then download it to your virtual machine.

- First look in the airlock to see if the model is already there
- If not, download it from Hugging Face, zip the folder
```bash
huggingface-cli download <HUGGING_FACE_MODEL> --local-dir ./models/<MODEL_NAME>
zip -r ./models/<MODEL_NAME>.zip ./models/<MODEL_NAME>
```
- Then upload/download to the airlock as documented in the [SAFEHR docs](https://github.com/SAFEHR-data/safehr-data-service-catalogue/blob/main/User-Guides/TRE/import-data-to-the-TRE-workspace.md#import-data-to-the-tre-workspace)

> **Prompt development:** You don't need a model to test your code locally on your laptop. You can build and preview your prompts over your input CSV using `--dry-run` (which doesn't require a model or GPU).

---

## Step 3: Edit `config.yaml`

Open `config.yaml` and set `model.model` to the path of your model directory:

```yaml
model:
  model: /path/to/your/model   # ← change this
```

Update any other parameters as needed.
These are directly passed to vLLM, so see the [vLLM docs](https://docs.vllm.ai/en/latest/api/vllm/#vllm.LLM) for details.

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

**Preview your prompt locally or in the TRE (recommended):**

```bash
python run.py --input data/example_input.csv --config config.yaml --dry-run
```

This prints the first formatted prompt without loading the model. This is perfect for local prompt development on your laptop before running in the TRE.

**Run the full job (in the TRE with GPU):**

```bash
python run.py --input data/example_input.csv --config config.yaml
```

---

## Outputs

Results are saved to `outputs/<timestamp>/`. This folder contains:

- **`<your_filename>.csv`** — your original data with two added columns:
  - **`prompt`** — the full formatted prompt sent to the model for that row
  - **`output`** — the model's response
- **`config.yaml`** — exact copy of the config used (audit trail)

---

## Troubleshooting

**Out of memory**
> Reduce `model.gpu_memory_utilization` (e.g. `0.7`) or use a quantized model.

**"Model directory not found"**
> Check `model.model` in `config.yaml` is the correct absolute path.

**"Input CSV is missing required column(s)"**
> Column names must be exactly `id` and `text` (lowercase).
