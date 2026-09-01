from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.data import mitbih
from src.data.mitbih import RECORD_IDS, _download_if_needed, build_inventory, load_lead_map


class Response(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


def test_download_skips_a_nonempty_existing_file(tmp_path: Path) -> None:
    destination = tmp_path / "100.hea"
    destination.write_bytes(b"existing")

    def should_not_open(_url: str) -> Response:
        raise AssertionError("existing files must not be downloaded again")

    assert not _download_if_needed("https://example.test/100.hea", destination, should_not_open)
    assert destination.read_bytes() == b"existing"


def test_download_replaces_an_empty_file_atomically(tmp_path: Path) -> None:
    destination = tmp_path / "100.hea"
    destination.touch()
    assert _download_if_needed(
        "https://example.test/100.hea", destination, lambda _url: Response(b"header")
    )
    assert destination.read_bytes() == b"header"
    assert not destination.with_suffix(".hea.part").exists()


def test_lead_map_covers_pinned_records_and_handles_114() -> None:
    lead_map = load_lead_map(Path("config/lead_selection.v1.json"))
    assert set(lead_map["records"]) == set(RECORD_IDS)
    assert lead_map["records"]["114"]["channel_index"] == 1
    assert lead_map["records"]["114"]["channel_name"] == "MLII"


def test_lead_map_rejects_missing_records(tmp_path: Path) -> None:
    invalid_map = tmp_path / "lead-map.json"
    invalid_map.write_text(
        '{"schema_version": 1, "dataset": {"id": "mitdb", "version": "1.0.0"}, "records": {}}'
    )
    with pytest.raises(ValueError, match="exactly"):
        load_lead_map(invalid_map)


def test_inventory_writes_provenance_counts_and_selected_leads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    for record_id in RECORD_IDS:
        (raw_dir / f"{record_id}.hea").touch()

    lead_map = load_lead_map(Path("config/lead_selection.v1.json"))

    def fake_header(record_path: str) -> SimpleNamespace:
        record_id = Path(record_path).name
        lead = lead_map["records"][record_id]
        channel_names = ["V1", "V2"]
        channel_names[lead["channel_index"]] = lead["channel_name"]
        return SimpleNamespace(n_sig=2, sig_name=channel_names, fs=360, sig_len=3600)

    monkeypatch.setattr(mitbih.wfdb, "rdheader", fake_header)
    monkeypatch.setattr(
        mitbih.wfdb, "rdann", lambda *_args: SimpleNamespace(symbol=["N", "V", "N"])
    )

    output = tmp_path / "manifest.json"
    manifest = build_inventory(raw_dir, Path("config/lead_selection.v1.json"), output)
    written = json.loads(output.read_text())

    assert len(manifest["records"]) == 48
    assert written["source"]["version"] == "1.0.0"
    assert written["records"][0]["annotation_counts_by_symbol"] == {"N": 2, "V": 1}
    record_114 = next(item for item in written["records"] if item["record_id"] == "114")
    assert record_114["selected_lead"]["channel_index"] == 1
