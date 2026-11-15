"""Integrity tests for the model bundle (no training data needed): hash list, tamper detection, root-hash pinning."""
import shutil, sys
from pathlib import Path
import pytest
MODEL = Path(__file__).resolve().parents[1] / "model"
sys.path.insert(0, str(MODEL))
from verify_bundle import verify_bundle, sha256_file, BundleIntegrityError, SUMS


def test_bundle_matches_hash_list():
    r = verify_bundle(MODEL)
    assert r["files"] >= 8 and r["root_sha256"] == sha256_file(MODEL / SUMS)
    listed = {l.split(None, 1)[1].strip() for l in (MODEL / SUMS).read_text().splitlines()}
    assert {"lgbm_w5.txt", "lgbm_w10.txt", "lgbm_w20.txt", "manifest.json", "mubsir_infer.py"} <= listed


def test_tampering_is_detected(tmp_path):
    d = tmp_path / "m"; shutil.copytree(MODEL, d, ignore=shutil.ignore_patterns("__pycache__"))
    verify_bundle(d)
    (d / "manifest.json").write_text((d / "manifest.json").read_text().replace('"version": "1.0"', '"version": "1.0"', 1) + " ")          # any byte change
    with pytest.raises(BundleIntegrityError, match="modified: manifest.json"): verify_bundle(d)
    shutil.copy(MODEL / "manifest.json", d / "manifest.json"); verify_bundle(d)
    (d / "lgbm_w10.txt").unlink()
    with pytest.raises(BundleIntegrityError, match="missing: lgbm_w10.txt"): verify_bundle(d)
    shutil.copy(MODEL / "lgbm_w10.txt", d / "lgbm_w10.txt"); (d / "extra_model.txt").write_text("x")
    with pytest.raises(BundleIntegrityError, match="unlisted file: extra_model.txt"): verify_bundle(d)


def test_root_hash_pin_catches_replaced_hash_list(tmp_path):
    root = sha256_file(MODEL / SUMS); verify_bundle(MODEL, expected_root_sha256=root)
    d = tmp_path / "m"; shutil.copytree(MODEL, d, ignore=shutil.ignore_patterns("__pycache__"))
    (d / "lgbm_w5.txt").write_text((d / "lgbm_w5.txt").read_text() + "\n")                  # swap a model AND regenerate the list: only the pinned root hash notices
    (d / SUMS).write_text("".join(f"{sha256_file(d / n)}  {n}\n" if n == "lgbm_w5.txt" else l + "\n" for l in (MODEL / SUMS).read_text().splitlines() for n in [l.split(None, 1)[1].strip()]))
    verify_bundle(d)                                                                       # the list is consistent with the files ...
    with pytest.raises(BundleIntegrityError, match="pinned root hash"): verify_bundle(d, expected_root_sha256=root)   # ... but not with the pinned hash
