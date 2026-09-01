# ECG Neural Network

An educational, non-clinical ECG beat-classification research project built around the MIT-BIH Arrhythmia Database.

## Scope

This project studies **expert-annotated individual ECG beats**, not whole-recording rhythm interpretation or patient diagnosis. V1 classifies annotation-centered beat windows as Normal or Abnormal; V2 will expand to five AAMI-style benchmark classes.

This software is for education and research only. It is not medical software, must not be used to make clinical decisions, and does not provide medical advice.

## Setup

Supported Python version: **3.11**.

```bash
python3 --version  # should report 3.11.x
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

In VS Code, install the Microsoft Jupyter extension, open `notebooks/01_exploring_ecg.ipynb`, and select the `.venv` Python kernel.

When tests are added in Phase 3, run them with:

```bash
python -m pytest
```

`requirements.txt` contains direct dependency constraints. Each training experiment will additionally save its exact resolved package versions, Python version, seed, data split, label mapping, and preprocessing configuration with its artifacts.

## Data

V1 and V2 use the **MIT-BIH Arrhythmia Database v1.0.0**. The raw files belong under `data/raw/` and are intentionally excluded from Git. Data acquisition will be implemented as a reproducible Phase 1 command; until then, obtain the data only from the official [PhysioNet dataset page](https://physionet.org/content/mitdb/1.0.0/).

The dataset is available under the [Open Data Commons Attribution License v1.0](https://opendatacommons.org/licenses/by/1-0/). Any report or derivative work using it should cite:

- Moody, G. B., & Mark, R. G. (2005). *MIT-BIH Arrhythmia Database* (version 1.0.0). PhysioNet. https://doi.org/10.13026/C2F305
- Moody, G. B., & Mark, R. G. (2001). *The impact of the MIT-BIH Arrhythmia Database*. IEEE Engineering in Medicine and Biology Magazine, 20(3), 45–50.

The dataset contains historical, two-channel ambulatory ECG excerpts and is not representative of clinical prevalence. Results must be reported as dataset-specific.

## Project documentation

See the [implementation plan](docs/implementation-plan.md), [domain glossary](CONTEXT.md), and [architecture decision records](docs/adr/). The plan defines the leakage-safe split, label mapping, evaluation protocol, and gates before any future local viewer can analyze unannotated WFDB data.

### Reproducible data inventory

After creating the virtual environment, acquire the pinned source files and
produce an inventory manifest:

```bash
.venv/bin/python -m src.data.cli acquire
.venv/bin/python -m src.data.cli inventory
```

`acquire` is idempotent: it downloads only missing or empty local files into
`data/raw/mitdb-1.0.0/`. `inventory` writes
`data/processed/mitdb_manifest.v1.json`, including WFDB header metadata,
reference-annotation counts, source provenance, and the selected lead. The
committed `config/lead_selection.v1.json` explicitly chooses MLII at index 1
for record 114 because its channel order is `V5`, `MLII`.

### Data exploration (Phase 2)

`notebooks/01_exploring_ecg.ipynb` is a narrative over the Phase 1 code. It reports
the raw annotation-symbol inventory, the mapped V1 (Normal/Abnormal) and V2
five-class distributions pooled and per record, excluded-annotation and
signal-quality notes, and per-candidate window-edge skip counts. Re-run it with:

```bash
.venv/bin/jupyter nbconvert --to notebook --execute --inplace notebooks/01_exploring_ecg.ipynb
```

The label mapping itself lives in `src/data/labels.py` (`map_v1`, `map_v2`,
`summarize_counts`) and is covered by `tests/test_labels.py`. The notebook's
decision gate output is `config/preprocessing_candidates.v1.json`: three
pre-registered asymmetric beat windows (more post-R than pre-R waveform) and one
band-pass filter configuration. Window, filter, and normalization choices remain
validation-only experiments.
