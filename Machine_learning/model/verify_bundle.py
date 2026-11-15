"""Integrity check for the Mubsir model bundle. Standard library only: run it BEFORE loading the models.

    python verify_bundle.py                       # checks this folder against SHA256SUMS.txt
    python verify_bundle.py --root-hash <sha256>  # also pins SHA256SUMS.txt itself to a hash you stored elsewhere

    from verify_bundle import verify_bundle
    verify_bundle("model", expected_root_sha256=CONFIG_ROOT_HASH)   # raises BundleIntegrityError on any mismatch

Why the root hash: SHA256SUMS.txt sits next to the files, so someone who can replace a model can replace the list too.
Store the root hash (sha256 of SHA256SUMS.txt, printed by this script and recorded in docs/RELEASE_HASHES.md) somewhere the model files'
writers cannot change (deployment config, signed git tag, the approval ticket). A `version` field in manifest.json proves nothing by itself."""
import hashlib, sys
from pathlib import Path

SUMS = "SHA256SUMS.txt"
IGNORED = {SUMS, "__pycache__"}


class BundleIntegrityError(RuntimeError):
    pass


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_sums(bundle_dir):
    sums = {}
    for line in (Path(bundle_dir) / SUMS).read_text().splitlines():
        if not line.strip():
            continue
        digest, name = line.split(None, 1); name = name.strip().lstrip("*")
        if Path(name).is_absolute() or ".." in Path(name).parts:
            raise BundleIntegrityError(f"unsafe path in {SUMS}: {name!r}")
        sums[name] = digest.lower()
    return sums


def verify_bundle(bundle_dir=None, expected_root_sha256=None, allow_extra_files=False):
    """Returns {'root_sha256': ..., 'files': n}. Raises BundleIntegrityError if the list is missing/altered, a file is missing/changed, or an unlisted file is present."""
    d = Path(bundle_dir or Path(__file__).resolve().parent)
    if not (d / SUMS).is_file():
        raise BundleIntegrityError(f"{SUMS} not found in {d}")
    root = sha256_file(d / SUMS)
    if expected_root_sha256 and root != expected_root_sha256.lower():
        raise BundleIntegrityError(f"{SUMS} does not match the pinned root hash (got {root})")
    sums = read_sums(d); problems = []
    for name, digest in sums.items():
        f = d / name
        if not f.is_file(): problems.append(f"missing: {name}")
        elif sha256_file(f) != digest: problems.append(f"modified: {name}")
    if not allow_extra_files:
        present = {p.relative_to(d).as_posix() for p in d.rglob("*") if p.is_file() and not (set(p.relative_to(d).parts) & IGNORED)}
        problems += [f"unlisted file: {n}" for n in sorted(present - set(sums))]
    if problems:
        raise BundleIntegrityError("; ".join(problems))
    return {"root_sha256": root, "files": len(sums)}


if __name__ == "__main__":
    args = sys.argv[1:]; root = None; folder = None
    while args:
        a = args.pop(0)
        if a == "--root-hash": root = args.pop(0)
        else: folder = a
    try:
        r = verify_bundle(folder, root)
        print(f"OK: {r['files']} files match {SUMS}; root hash {r['root_sha256']}" + ("  (pinned hash matched)" if root else "  (no pinned root hash given)"))
    except BundleIntegrityError as e:
        print(f"FAILED: {e}"); sys.exit(1)
