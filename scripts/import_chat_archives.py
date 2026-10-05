#!/usr/bin/env python3
"""Restore exact historical study archives; no networking and no git writes.
Verifies every archive and existing destination before writing. Differing files
are never overwritten. All entries must remain inside their declared study root.
"""
import argparse
import hashlib
import json
import stat
import sys
import zipfile
from pathlib import Path, PurePosixPath


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-dir", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path,
                        default=Path(__file__).resolve().parents[1])
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    root = args.repo_root.resolve()
    manifest = json.loads((root / "archives_manifest.json").read_text())
    planned, existing = [], 0
    seen = set()
    # First pass validates all archives and destination conflicts before writes.
    for archive in manifest["archives"]:
        source = args.archive_dir.expanduser() / archive["filename"]
        if not source.is_file():
            raise FileNotFoundError(f"Missing original archive: {source}")
        if source.stat().st_size != archive["size_bytes"] or sha256(source) != archive["sha256"]:
            raise ValueError(f"Archive checksum mismatch: {source}; do not substitute a different ZIP")
        with zipfile.ZipFile(source) as z:
            entries = [info for info in z.infolist() if not info.is_dir()]
            if len(entries) != archive["file_count"]:
                raise ValueError(f"Unexpected file count in {source}")
            if sum(info.file_size for info in entries) != archive["uncompressed_bytes"]:
                raise ValueError(f"Unexpected uncompressed size in {source}")
            for info in entries:
                p = PurePosixPath(info.filename)
                if p.is_absolute() or ".." in p.parts or "\\" in info.filename or not p.parts or p.parts[0] != archive["root"]:
                    raise ValueError(f"Unsafe archive member: {info.filename}")
                if stat.S_ISLNK(info.external_attr >> 16):
                    raise ValueError(f"Symlink archive entry forbidden: {info.filename}")
                target = root.joinpath(*p.parts)
                if target.resolve() != target.absolute() or root not in target.resolve().parents:
                    raise ValueError(f"Symlink/path escape at {target}")
                if str(p) in seen:
                    raise ValueError(f"Duplicate archive destination: {p}")
                seen.add(str(p))
                content = z.read(info)  # validates ZIP CRC
                digest = hashlib.sha256(content).hexdigest()
                if target.exists():
                    if not target.is_file() or sha256(target) != digest:
                        raise ValueError(f"Existing file differs: {target}; preserve it and import into a clean clone")
                    existing += 1
                else:
                    planned.append((source, info.filename, target, digest))
    if args.verify_only:
        print(json.dumps({"status": "VERIFIED", "archive_files": len(seen),
                          "matching_existing": existing, "would_create": len(planned)}, indent=2))
        return
    for source, name, target, digest in planned:
        target.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(source) as z, target.open("xb") as stream:
            stream.write(z.read(name))
        if sha256(target) != digest:
            raise ValueError(f"Post-write checksum mismatch: {target}")
    print(json.dumps({"status": "IMPORTED_AND_VERIFIED", "archive_files": len(seen),
                      "matching_existing": existing, "created": len(planned),
                      "market_data_downloaded": False, "git_changed_automatically": False}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"IMPORT STOPPED: {exc}", file=sys.stderr)
        sys.exit(1)
