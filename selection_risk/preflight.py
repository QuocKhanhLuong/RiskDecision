"""Inventory local evidence without opening prior market outcome metrics."""
import csv
import json
from pathlib import Path
import re
import subprocess
import zipfile

from .runtime import ROOT, atomic_json, digest, environment, object_hash, utc


def seed_audit(out, config):
    candidates = set(range(config["seeds"]["start"], config["seeds"]["stop"]))
    candidates.add(config["microbenchmark_seed"])
    files, collisions, observed = {}, [], set()
    # Include ignored prior local run configs/manifests, raw seed CSVs and source;
    # do not read market outcome values. Snapshot seed filenames are sufficient
    # in addition to the immutable historical source/config manifests.
    for path in ROOT.rglob("*"):
        rel = path.relative_to(ROOT)
        if any(p in {".git", ".venv", "__pycache__", ".pytest_cache", "data"} for p in rel.parts):
            continue
        if not path.is_file() or "selection_risk" in rel.parts or "historical_snapshot" in rel.parts:
            continue
        match = re.search(r"_(\d+)\.(?:npz|json)$", path.name)
        if match:
            observed.add(int(match[1]))
        if path.suffix not in {".json", ".py", ".yaml", ".yml", ".csv"}:
            continue
        if path.stat().st_size > 20_000_000:
            continue
        files[str(rel)] = digest(path)
        if path.suffix == ".csv":
            with path.open() as stream:
                reader = csv.DictReader(stream)
                fields = [k for k in (reader.fieldnames or []) if "seed" in k.lower()]
                if not fields:
                    continue
                for row in reader:
                    for k in fields:
                        if row[k] and row[k].isdigit():
                            observed.add(int(row[k]))
        else:
            text = path.read_text(errors="replace")
            # Conservative literal audit covers seeds and range endpoints in code.
            # It cannot prove uniqueness against unavailable external artifacts.
            observed.update(int(s) for s in re.findall(r"(?<![\w.])\d+(?![\w.])", text))
            if path.suffix == ".json":
                def ranges(value, parent=""):
                    if isinstance(value, dict):
                        if "seed" in parent.lower() and {"start", "stop"} <= value.keys():
                            for seed in candidates:
                                if int(value["start"]) <= seed < int(value["stop"]):
                                    collisions.append({"file": str(rel), "seed": seed, "kind": "range"})
                        for k, v in value.items():
                            ranges(v, parent + "." + k)
                    elif isinstance(value, list):
                        for v in value:
                            ranges(v, parent)
                ranges(json.loads(text))
    collisions += [{"seed": seed, "kind": "literal_or_filename"} for seed in sorted(candidates & observed)]
    if collisions:
        raise ValueError(f"Proposed seeds collide with local evidence: {collisions}")
    result = {"utc": utc(), "status": "NO_LOCAL_COLLISION_FOUND", "candidate_seeds": sorted(candidates),
              "config_sha256": object_hash(config), "scanned_files": files,
              "scanned_file_count": len(files), "collisions": collisions,
              "scope": "Available local source/config/manifest seed fields and filenames; does not certify unseen external runs. Prior market outcome metrics not read for model selection."}
    atomic_json(Path(out) / "seed_audit.json", result)
    return result


def preflight(out, archive_dir, config):
    out = Path(out)
    manifest = json.loads((ROOT / "archives_manifest.json").read_text())
    imported, archive_rows = {}, []
    snapshot = out / "historical_snapshot"
    for archive in manifest["archives"]:
        path = Path(archive_dir) / archive["filename"]
        if digest(path) != archive["sha256"] or path.stat().st_size != archive["size_bytes"]:
            raise ValueError("Original archive verification failed")
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist() if not n.endswith("/")]
            if len(names) != archive["file_count"]:
                raise ValueError("Archive file count differs")
            import hashlib
            for name in names:
                expected = hashlib.sha256(z.read(name)).hexdigest()
                if digest(snapshot / name) != expected:
                    raise ValueError(f"Imported historical bytes differ: {name}")
                imported[name] = expected
        archive_rows.append(dict(archive, status="VERIFIED"))
    protected_names = subprocess.check_output(["git", "ls-files", "quant_research_v2", "quant_tailrisk_pilot",
                                              "archives_manifest.json", "scripts/import_chat_archives.py", "archive"],
                                             cwd=ROOT, text=True).splitlines()
    protected = {name: digest(ROOT / name) for name in protected_names}
    old = out / "preflight.json"
    result = {"utc": utc(), "base_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "environment": environment(), "archives": archive_rows, "imported_files": imported,
              "protected_tracked_files": protected,
              "review_zip": "MISSING in declared Downloads/import bundle; numeric comparison uses RESEARCH_STATE reported rounded values",
              "prior_local_runs": sorted(p.name for p in (ROOT / "runs").iterdir() if p.name != "selection_risk")}
    if old.exists():
        before = json.loads(old.read_text())
        if before["protected_tracked_files"] != protected or before["imported_files"] != imported:
            raise ValueError("Historical files changed since preflight")
        return before
    atomic_json(old, result)
    seed_audit(out, config)
    return result
