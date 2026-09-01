"""Reproducible local acquisition and inventory of MIT-BIH v1.0.0."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import BinaryIO, Callable
from urllib.request import urlopen

import wfdb

DATASET_ID = "mitdb"
DATASET_VERSION = "1.0.0"
DATASET_URL = f"https://physionet.org/files/{DATASET_ID}/{DATASET_VERSION}"
ANNOTATION_EXTENSION = "atr"
REQUIRED_EXTENSIONS = (".hea", ".dat", ".atr")

# A fixed corpus prevents an upstream RECORDS-file change from silently
# changing V1's dataset.
RECORD_IDS = (
    "100", "101", "102", "103", "104", "105", "106", "107", "108", "109",
    "111", "112", "113", "114", "115", "116", "117", "118", "119", "121",
    "122", "123", "124", "200", "201", "202", "203", "205", "207", "208",
    "209", "210", "212", "213", "214", "215", "217", "219", "220", "221",
    "222", "223", "228", "230", "231", "232", "233", "234",
)

DEFAULT_RAW_DIR = Path("data/raw/mitdb-1.0.0")
DEFAULT_LEAD_MAP_PATH = Path("config/lead_selection.v1.json")
DEFAULT_MANIFEST_PATH = Path("data/processed/mitdb_manifest.v1.json")
Opener = Callable[[str], BinaryIO]


def _download_if_needed(url: str, destination: Path, opener: Opener = urlopen) -> bool:
    """Download a file atomically unless a non-empty local copy already exists."""
    if destination.is_file() and destination.stat().st_size > 0:
        return False

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    temporary.unlink(missing_ok=True)
    try:
        with opener(url) as response, temporary.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        if temporary.stat().st_size == 0:
            raise ValueError(f"Downloaded an empty file from {url}")
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return True


def acquire(raw_dir: Path = DEFAULT_RAW_DIR, opener: Opener = urlopen) -> dict[str, object]:
    """Acquire source headers, signals, and reference annotations safely to rerun."""
    downloaded: list[str] = []
    skipped: list[str] = []
    for record_id in RECORD_IDS:
        for extension in REQUIRED_EXTENSIONS:
            filename = f"{record_id}{extension}"
            changed = _download_if_needed(f"{DATASET_URL}/{filename}", raw_dir / filename, opener)
            (downloaded if changed else skipped).append(filename)
    return {
        "dataset_id": DATASET_ID,
        "dataset_version": DATASET_VERSION,
        "raw_dir": str(raw_dir),
        "downloaded": downloaded,
        "skipped": skipped,
    }


def load_lead_map(path: Path = DEFAULT_LEAD_MAP_PATH) -> dict[str, object]:
    """Load and validate the committed per-record lead-selection map."""
    lead_map = json.loads(path.read_text())
    if lead_map.get("schema_version") != 1:
        raise ValueError("Lead map must use schema_version 1")
    if lead_map.get("dataset") != {"id": DATASET_ID, "version": DATASET_VERSION}:
        raise ValueError("Lead map dataset must be MIT-BIH v1.0.0")
    records = lead_map.get("records")
    if not isinstance(records, dict) or set(records) != set(RECORD_IDS):
        raise ValueError("Lead map must contain exactly the 48 MIT-BIH V1 record IDs")
    return lead_map


def _record_inventory(raw_dir: Path, record_id: str, lead: dict[str, object]) -> dict[str, object]:
    header = wfdb.rdheader(str(raw_dir / record_id))
    annotation = wfdb.rdann(str(raw_dir / record_id), ANNOTATION_EXTENSION)
    channel_index = lead["channel_index"]
    channel_name = lead["channel_name"]
    if not isinstance(channel_index, int) or not 0 <= channel_index < header.n_sig:
        raise ValueError(f"{record_id}: lead-map channel index is invalid")
    if header.sig_name[channel_index] != channel_name:
        raise ValueError(
            f"{record_id}: expected {channel_name!r} at index {channel_index}, "
            f"found {header.sig_name[channel_index]!r}"
        )
    return {
        "record_id": record_id,
        "sampling_frequency_hz": header.fs,
        "signal_length_samples": header.sig_len,
        "duration_seconds": header.sig_len / header.fs,
        "channel_names": header.sig_name,
        "selected_lead": {
            "channel_index": channel_index,
            "channel_name": channel_name,
            "rationale": lead["rationale"],
        },
        "annotation_counts_by_symbol": dict(sorted(Counter(annotation.symbol).items())),
    }


def build_inventory(
    raw_dir: Path = DEFAULT_RAW_DIR,
    lead_map_path: Path = DEFAULT_LEAD_MAP_PATH,
    output_path: Path = DEFAULT_MANIFEST_PATH,
) -> dict[str, object]:
    """Read local WFDB files and write a machine-readable, versioned manifest."""
    lead_map = load_lead_map(lead_map_path)
    missing = [record_id for record_id in RECORD_IDS if not (raw_dir / f"{record_id}.hea").is_file()]
    if missing:
        raise FileNotFoundError(
            f"Missing {len(missing)} MIT-BIH headers in {raw_dir}; run acquire first. "
            f"First missing record: {missing[0]}"
        )
    manifest = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "dataset": "MIT-BIH Arrhythmia Database",
            "dataset_id": DATASET_ID,
            "version": DATASET_VERSION,
            "url": DATASET_URL,
            "doi": "10.13026/C2F305",
            "annotation_extension": ANNOTATION_EXTENSION,
        },
        "lead_map": {"path": str(lead_map_path), "version": lead_map["map_version"]},
        "records": [
            _record_inventory(raw_dir, record_id, lead_map["records"][record_id])
            for record_id in RECORD_IDS
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    temporary.replace(output_path)
    return manifest
