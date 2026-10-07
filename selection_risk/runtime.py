"""Immutable run identity, atomic per-instance checkpoints and progress receipts."""
from contextlib import contextmanager
from datetime import datetime, timezone
import csv
import fcntl
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def object_hash(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    tmp.replace(path)


def write_csv(path, rows):
    if not rows:
        raise ValueError("Refuse empty result CSV")
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def environment():
    return {"python": sys.version, "platform": platform.platform(), "device": "CPU",
            "packages": {name: importlib.metadata.version(name) for name in
                         ("numpy", "scipy", "scikit-learn", "pytest", "tqdm")},
            "threads": {k: os.environ.get(k) for k in
                        ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                         "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")}}


def source_hashes():
    paths = list((ROOT / "selection_risk").glob("*.py"))
    paths += [ROOT / "selection_risk/OIC_APPLICABILITY.md",
              ROOT / "quant_research_v2/src/research.py"]
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)}


class Run:
    def __init__(self, out, config, inputs):
        self.out = Path(out)
        self.out.mkdir(parents=True, exist_ok=True)
        self.config = config
        self.identity = {"config": config, "sources": source_hashes(),
                         "environment": environment(), "inputs": inputs}
        self.fingerprint = object_hash(self.identity)

    @contextmanager
    def session(self):
        with (self.out / ".lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            frozen = self.out / "freeze.json"
            if frozen.exists():
                old = json.loads(frozen.read_text())
                if old["fingerprint"] != self.fingerprint or old["identity"] != self.identity:
                    raise ValueError("Resume rejected: code/config/environment/input identity changed")
            else:
                atomic_json(frozen, {"created_utc": utc(), "fingerprint": self.fingerprint,
                                     "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                                     "identity": self.identity})
            self.started = time.perf_counter()
            self.event("session_start", fingerprint=self.fingerprint)
            try:
                yield self
            except BaseException as exc:
                self.event("session_interrupted", error=repr(exc), seconds=time.perf_counter()-self.started)
                raise
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def event(self, event, **fields):
        with (self.out / "progress.jsonl").open("a") as stream:
            stream.write(canonical(dict(utc=utc(), event=event, **fields)) + "\n")
            stream.flush()

    def case(self, key):
        path = self.out / "cases" / (key + ".json")
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        if data["fingerprint"] != self.fingerprint or object_hash(data["payload"]) != data["payload_sha256"]:
            raise ValueError("Corrupt/mismatched case checkpoint")
        for filename, expected in data["payload"].get("artifacts", {}).items():
            if digest(self.out / filename) != expected:
                raise ValueError("Corrupt case artifact")
        return data["payload"]

    def save(self, key, payload):
        atomic_json(self.out / "cases" / (key + ".json"),
                    {"fingerprint": self.fingerprint, "payload": payload,
                     "payload_sha256": object_hash(payload)})

    def finish(self, rows, cases, executed, resumed, complete):
        receipt = {"status": "COMPLETE" if complete else "PARTIAL_RESUMABLE",
                   "fingerprint": self.fingerprint, "cases_present": cases,
                   "cases_executed_this_session": executed, "cases_resumed": resumed,
                   "crossed_rows": len(rows), "session_seconds": time.perf_counter()-self.started,
                   "finished_utc": utc()}
        atomic_json(self.out / "receipt.json", receipt)
        self.event("session_end", **receipt)
        return receipt
