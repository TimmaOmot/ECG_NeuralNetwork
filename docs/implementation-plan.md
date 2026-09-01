# ECG Beat Classification Implementation Plan

## Purpose and boundary

Build an educational and research system for **classifying individual, expert-annotated ECG beats**. It is not a diagnostic system, does not infer a patient's rhythm from a whole recording, and must state that it is not for clinical use.

V1 uses the MIT-BIH Arrhythmia Database only. It classifies an annotation-centered beat window as **Normal** or **Abnormal**. V2 expands this to five AAMI-style benchmark superclasses. A local viewer is a later milestone; it must accept WFDB data only, persist no user data, and must not analyze unannotated recordings until beat detection and external validation have been completed.

The terms and durable decisions behind this plan live in [CONTEXT.md](../CONTEXT.md) and [the ADRs](adr/).

## Non-negotiable research rules

- Use MIT-BIH Arrhythmia Database **v1.0.0** and preserve its required attribution and citation. The data are local, untracked, and acquired reproducibly from the [PhysioNet dataset page](https://physionet.org/content/mitdb/1.0.0/).
- Split before extracting training examples. Never randomly split individual beats.
- Use a fixed custom participant-grouped partition. Records `201` and `202` must be in the same partition because they are from one participant; do not describe this as the usual DS1/DS2 benchmark.
- Fit every learned preprocessing statistic on training data only. Validation selects experiments; the test set is used only at the final test stage.
- Preserve the lead-selection map, split ID, label mapping, preprocessing configuration, package versions, random seed, metrics, and confusion matrix with every model artifact.
- Keep notebooks for exploration and presentation. Put reusable logic in `src/` and protect it with `tests/`.

## V1 data contract

### Source

MIT-BIH contains 48 approximately 30-minute, two-channel records from 47 participants at 360 Hz. Each example is a fixed-duration window centered on an expert beat annotation—not a whole recording and not an automatically detected beat. [PhysioNet documentation](https://physionet.org/physiobank/database/html/mitdbdir/intro.htm)

### Labels

The V1 binary target is an explicit benchmark convention:

| V1 target | MIT-BIH annotation symbols |
| --- | --- |
| Normal | `N`, `L`, `R`, `e`, `j` |
| Abnormal | `A`, `a`, `J`, `S`, `V`, `E`, `F` |
| Excluded | `/`, `f`, `Q`, and all non-beat/quality/rhythm markers |

V2 retains this mapping and exposes five classes: `N={N,L,R,e,j}`, `S={A,a,J,S}`, `V={V,E}`, `F={F}`, and `Q={/,f,Q}`. This is a documented MIT-BIH benchmark convention, not a claim that every non-N annotation is clinically equivalent. [MIT-BIH annotation symbols](https://physionet.org/physiobank/database/html/mitdbdir/intro.htm#Annotations)

### Signal selection and examples

- Create a versioned per-record lead-selection map that prefers documented MLII; record exceptions rather than assuming channel 0 is always the chosen lead.
- Exclude only annotations outside the V1 mapping. Retain valid mapped beats in records that also contain paced or excluded annotations.
- Skip any annotation whose requested window would extend beyond its recording boundary. Count and report skipped annotations.
- In Phase 2, pre-register three asymmetric candidate windows in seconds, each containing more post-R-peak than pre-R-peak waveform. Choose the exact candidates after inspecting the data and before training any model.
- Compare raw signal against one documented band-pass filtering configuration. Treat filtering, window choice, and per-window normalization as validation-only experiments.
- The default normalization fits statistics on the training partition and applies them unchanged to validation and test partitions. It must not use test-set statistics.

## Phased work

### Phase 0 — Make the repository reproducible

1. Update `.gitignore` to exclude `data/raw/`, `data/processed/`, model artifacts, notebook checkpoints, and local environments.
2. Set Python 3.11 as the supported runtime.
3. Populate `requirements.txt` with direct dependencies: `wfdb`, `numpy`, `pandas`, `scipy`, `matplotlib`, `scikit-learn`, `torch`, `ipykernel`, and `pytest`.
4. Record project setup, dataset attribution, non-clinical scope, and how to run each phase in `README.md`.

**Done when:** a clean environment can install dependencies and run the test suite; raw data is not staged by Git.

### Phase 1 — Acquire and inventory MIT-BIH

1. Implement an idempotent download/verification command in `src/data/` that pins MIT-BIH v1.0.0 and writes into `data/raw/`.
2. Read WFDB headers and annotations for every record.
3. Produce a machine-readable manifest containing record ID, sampling frequency, channel descriptions, selected lead, annotation counts by raw symbol, and data/version provenance.
4. Create the first version of the lead-selection map. Explicitly inspect exceptional recordings, including record 114's reversed signals.

**Done when:** the manifest covers all source records, names every selected lead, and can be rebuilt without a notebook.

### Phase 2 — Explore the source data

Use `notebooks/01_exploring_ecg.ipynb` as a narrative over the Phase 1 code. It should:

1. Plot a full recording and several zoomed segments.
2. Overlay expert annotation locations and labels.
3. Show sampling frequency, duration, channels, raw annotation symbols, included/excluded counts, and mapped V1/V2 class distributions.
4. Summarize class counts by record, lead availability, annotations skipped at window edges, and any signal-quality concerns.
5. Select and commit the pre-registered candidate windows and filtering configuration for V1 experiments.

**Decision gate:** do not create a split or fit a model until this notebook has reported the mapped distribution and the candidate preprocessing configuration is written into versioned config.

### Phase 3 — Build the deterministic dataset contract

1. Implement label mapping, exclusion, lead selection, window extraction, filtering, and training-only normalization under `src/data/` and `src/preprocessing/`.
2. Create one fixed custom split after inspecting per-record mapped counts. Target approximately 60%/20%/20% train/validation/test while favoring coverage of less-common included labels and keeping participant groups together.
3. Version the exact record IDs, grouping rule, split algorithm/seed, label mapping, and preprocessing candidate IDs in configuration files.
4. Build dataset objects that return a waveform, binary label, original annotation symbol, record ID, participant-group ID, and provenance needed for analysis.
5. Add tests for label mapping, excluded symbols, 201/202 isolation, deterministic split generation, window bounds, selected lead use, and training-only normalization.

**Done when:** the same input/versioned configuration deterministically produces the same train, validation, and test example manifests; no participant group crosses a partition.

### Phase 4 — Establish the non-neural baseline

1. Flatten the same normalized beat windows that the CNN will receive.
2. Train logistic regression with the fixed split.
3. Compare unweighted and class-weighted loss/estimation without oversampling.
4. Choose a probability threshold on validation macro F1, then freeze it with the selected preprocessing configuration.
5. Save the model and its full experiment bundle.

**Done when:** the baseline has reproducible validation metrics, a threshold chosen without test access, and artifacts sufficient to recreate predictions.

### Phase 5 — Train the V1 1D CNN

1. Implement one shallow two-block 1D CNN in `src/models/`; keep CNN-LSTM, attention, and transformer variants out of V1.
2. Use the same split, examples, candidate preprocessing choices, and threshold-selection rule as the baseline.
3. Run a narrow validation-only search over agreed training/model parameters, including the unweighted versus class-weighted loss comparison.
4. Run every selected configuration with three fixed seeds; aggregate validation macro F1 to choose the final configuration.
5. Select each seed's best validation checkpoint. Do not retrain on train-plus-validation before the V1 test stage.

**Done when:** CNN and baseline have directly comparable validation results with recorded configuration and seed information.

### Phase 6 — Final V1 evaluation and report

1. Freeze all choices, then perform the single final test stage for the selected baseline and CNN across their three fixed seeds.
2. Report test accuracy, macro F1, abnormal-class precision/recall/F1, sensitivity, specificity, balanced accuracy, support, and confusion matrices.
3. Report pooled and per-record results, original-symbol error breakdowns, and record-aware bootstrap confidence intervals. Do not let correlated beats create artificially narrow beat-level uncertainty claims.
4. Report mean and variation over the three seeds.
5. Write a concise limitations section: historical single-institution data, deliberately enriched arrhythmia records, annotation-centered inputs, participant grouping assumptions, and no clinical applicability.

**Done when:** the report compares CNN against baseline on an untouched test partition and another person can reproduce the reported run from the recorded bundle.

### Phase 7 — V2 five-class classification

1. Extend the label mapping to N/S/V/F/Q and re-run the complete split-aware pipeline.
2. Reassess class support before deciding whether class weighting alone is adequate; any sampling strategy is a separately documented validation-only experiment.
3. Report per-class precision, recall, F1, support, and a five-class confusion matrix. Do not substitute accuracy for rare-class performance.

**Done when:** the five-class result is evaluated with the same leakage controls and is compared against an appropriate multiclass baseline.

### Phase 8 — Explainability and external validation

1. Add Integrated Gradients for the 1D CNN after V2, initially as a research visualization.
2. Show the waveform, attribution, prediction, confidence, model version, and explicit statement that attribution is not clinical evidence.
3. Select and document a separate external ECG dataset for evaluation. Adapt only through a clearly stated protocol; do not silently merge it with MIT-BIH.
4. Compare external results with MIT-BIH results and document distribution-shift limitations.

**Done when:** model attributions are reproducible and external-dataset performance is reported before enabling unannotated-record analysis.

### Phase 9 — Local educational viewer

1. Keep framework selection provisional until the model input/output artifact contract is stable.
2. First provide a local, non-persistent WFDB viewer for annotated research records: waveform display, selected lead, beat window, prediction, confidence, and attribution where available.
3. Add an automated beat detector only after Phase 8. Validate the full detector-plus-classifier pipeline externally before accepting unannotated WFDB records.
4. Do not host a public upload service or present the output as medical advice.

**Done when:** the local viewer is usable with the documented research workflow and clearly communicates its scope and limitations.

## Expected module seams

| Area | Responsibilities |
| --- | --- |
| `src/data/` | download, WFDB indexing, source manifests, lead map, label mapping, participant-grouped split |
| `src/preprocessing/` | window extraction, filtering, normalization, example manifests |
| `src/models/` | logistic-regression adapter, shallow 1D CNN, model artifact interfaces |
| `src/training/` | configuration loading, deterministic runners, checkpointing, experiment bundles |
| `src/evaluation/` | threshold selection, metrics, confusion matrices, record-aware uncertainty, reports |
| `tests/` | data-contract and leakage tests, deterministic preprocessing/split tests, metric tests |

## Experiment bundle

Every evaluated run stores:

- weights/checkpoint and model configuration;
- source dataset version and acquisition provenance;
- lead-selection-map version, label-map version, split ID, and preprocessing configuration;
- exact package versions, Python version, and seed;
- validation selection result, test metrics, confusion matrix, predictions, and record-level summaries.

## Explicit anti-goals

- No random heartbeat-level splitting.
- No use of validation/test statistics for preprocessing.
- No test-set-driven tuning or repeated test-set experiments.
- No claim to diagnose a person or interpret a complete rhythm in V1.
- No unannotated WFDB analysis before automatic beat detection plus external validation.
- No public upload/storage service in the initial application.
