# ECG Beat Classification

This project studies how to classify annotated heartbeats from ECG recordings for educational and research use. It is not a clinical diagnostic system.

## Language

**ECG recording**:
A time-series ECG signal and its associated metadata from one MIT-BIH record.
_Avoid_: Patient ECG, sample

**Beat annotation**:
An expert-provided label and time location for an individual heartbeat in an ECG recording.
_Avoid_: Ground truth rhythm, diagnosis

**Included beat annotation**:
A beat annotation that belongs to the project's fixed AAMI-style label mapping and can become a training or evaluation example.
_Avoid_: Every annotation, all beats

**Excluded annotation**:
An annotation outside the project's fixed label mapping, such as a non-beat marker, unsupported type, or artifact; it is not assigned to the abnormal class.
_Avoid_: Abnormal beat

**Beat window**:
A fixed-length ECG segment centered on a beat annotation; it is one model input.
_Avoid_: ECG recording, rhythm strip

**Lead-selection map**:
A versioned mapping from each MIT-BIH record to the waveform channel selected for beat-window extraction, preferring documented MLII and recording any exception.
_Avoid_: Always channel 0

**Beat classification**:
The task of assigning a class to one annotated beat window. It is not an interpretation of an entire recording or a patient diagnosis.
_Avoid_: Arrhythmia diagnosis, rhythm classification

**Normal beat**:
A beat assigned to the project's normal class under its documented label-mapping rules.
_Avoid_: Healthy patient, normal ECG

**Abnormal beat**:
Any included beat not assigned to the normal class in the binary classification version.
_Avoid_: Arrhythmia, abnormal patient

**N superclass**:
The project's documented grouping of `N`, `L`, `R`, `e`, and `j` beat symbols for its normal class.
_Avoid_: Every normal-looking beat

**Abnormal superclass**:
The project's documented grouping of the `S`, `V`, and `F` AAMI-style beat superclasses for binary classification.
_Avoid_: All non-N annotations

**Annotation-centered pipeline**:
A research pipeline that creates beat windows from expert beat annotations. It does not locate beats in an unannotated recording.
_Avoid_: Automated ECG analysis, beat detector

**Inter-patient split**:
An evaluation partition in which all records from one participant belong to exactly one of training, validation, or test.
_Avoid_: Random beat split, record-level split

**Canonical record-disjoint benchmark**:
A published MIT-BIH record partition that does not necessarily keep all records from one participant together.
_Avoid_: Inter-patient split

**WFDB record**:
An ECG recording represented in the WaveForm DataBase format, including signal and annotation files.
_Avoid_: Arbitrary upload, ECG image
