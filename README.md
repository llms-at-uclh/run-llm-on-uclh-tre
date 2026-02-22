# Run LLM on UCLH TRE

This repo is our current best practice for running a local large language model (LLM) on a batch of clinical text in the UCLH TRE.

## Projects Using This Code

*(List of projects will be added here...)*

If you use this repository for your research, please let us know so we can add your project to this list!

---

## Table of Contents

- [Getting Started](#getting-started)
- [Repository Layout](#repository-layout)
- [Workflow Steps](#workflow-steps)
  - [1. Install dependencies](#1-install-dependencies)
  - [2. Download a model (in the TRE)](#2-download-a-model-in-the-tre)
  - [3. Configure the run](#3-configure-the-run)
  - [4. Prepare your input CSV](#4-prepare-your-input-csv)
  - [5. Run the pipeline](#5-run-the-pipeline)
- [Outputs](#outputs)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Projects Using This Code](#projects-using-this-code)
- [Citation and Acknowledgements](#citation-and-acknowledgements)
- [Contact](#contact)

---

## Getting Started

This repository is a starting point. We recommend **forking** it for your own research projects to safely modify prompts and configurations while maintaining version control. If you fix a bug, improve documentation, or add a generally useful feature to `run.py`, please **contribute** it back via a Pull Request.

**If you are new to this:**
1. Clone the repository to your local machine for prompt development.
2. Use the `--dry-run` flag to test your prompts without needing a GPU or downloading a model.
3. Read the vLLM docs for [LLMs](https://docs.vllm.ai/en/latest/api/vllm/#vllm.LLM) and [SamplingParams](https://docs.vllm.ai/en/latest/api/vllm/#vllm.SamplingParams) to understand the configuration options.
4. Follow the workflow steps below to run it in the TRE.

---

## Repository Layout

```text
run-llm-on-uclh-tre/
├── config.yaml           ← Model configuration (model path, parameters)
├── prompt.py             ← Edit this: what you want the model to do
├── run.py                ← Main script (do not edit unless required)
├── requirements.txt      ← Python dependencies
├── data/
│   └── example_input.csv ← Example input file
└── outputs/              ← Created automatically when you run the script
```

![Data flow diagram](./figures/data_flow.svg)


---

## Workflow Steps

### 1. Install dependencies

Open a terminal in the repository folder and run:

```bash
python -m venv .venv
source .venv/bin/activate       # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
> **TRE Note:** Packages are installed from the internal Nexus mirror. Contact your TRE administrator to request missing packages.

### 2. Download a model (in the TRE)

Check the airlock to see if the model is already available. If not, download it from Hugging Face on a machine with internet access, zip the folder, and upload it to the airlock:

```bash
huggingface-cli download <HUGGING_FACE_MODEL> --local-dir ./models/<MODEL_NAME>
zip -r ./models/<MODEL_NAME>.zip ./models/<MODEL_NAME>
```
Follow the [SAFEHR docs](https://github.com/SAFEHR-data/safehr-data-service-catalogue/blob/main/User-Guides/TRE/import-data-to-the-TRE-workspace.md#import-data-to-the-tre-workspace) to import the zipped data to your virtual machine in the TRE.

### 3. Configure the run

Update `config.yaml` with the absolute path to your model directory:
```yaml
model:
  model: /path/to/your/model
```

Edit `prompt.py` to define the `SYSTEM_PROMPT` and user messages. Use `{text}` to insert content from the CSV row:
```python
{"role": "user", "content": f"Summarise the following:\n\n{text}"}
```

### 4. Prepare your input CSV

Your input file must contain exactly two columns with lowercase headers: `id` and `text`. See `data/example_input.csv` for an example.

### 5. Run the pipeline

**Local prompt preview (no GPU or model required):**
```bash
python run.py --input data/example_input.csv --config config.yaml --dry-run
```

**Full job (in the TRE with GPU):**
```bash
python run.py --input data/example_input.csv --config config.yaml
```

---

## Outputs

Results are saved to `outputs/<timestamp>/`, containing:
- `<your_filename>.csv` — your original data plus `prompt` and `output` columns representing the model's response.
- `config.yaml` — an exact copy of the configuration used for auditability.

---

## Troubleshooting

- **Out of memory:** Reduce `model.gpu_memory_utilization` in `config.yaml` (e.g., to `0.7`) or use a quantized model.
- **Model directory not found:** Check `model.model` in `config.yaml` is the correct absolute path.
- **Input CSV is missing required column(s):** Ensure column names are exactly `id` and `text` (lowercase).

---

## Contributing

Contributions are welcome! If you are modifying the code or documentation, please follow these steps:

1. **Pre-commit hooks:** We use `pre-commit` to maintain code formatting.
   ```bash
   pip install pre-commit
   pre-commit install
   ```
2. **Updating requirements:** We use `pip-tools` to manage dependencies. If you add or alter top-level dependencies, update `requirements.in` and run:
   ```bash
   pip-compile requirements.in
   ```
3. **Spelling:** Please use British English spelling for all documentation, guides, or comments (e.g., "programme", "summarise", "colour").

---

## Citation and Acknowledgements

If you use this code in your work, please acknowledge it. We recommend citing it as follows:

```bibtex
@misc{run-llm-on-uclh-tre,
  author = {Simon Ellershaw},
  title = {Run LLM on UCLH TRE},
  year = {2026},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/llms-at-uclh/run-llm-on-uclh-tre}}
}
```

---

## Contact

For questions, support, or to notify us that you are using this code, please contact:

- <simon.ellershaw.20@ucl.ac.uk>
- Or simply open an Issue or Pull Request in this repository!
