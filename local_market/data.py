"""Official latest-vintage FX data, immutable raw bytes and explicit gap audit."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import zipfile

import numpy as np

PANELS = {"ecb": ["USD", "JPY", "GBP", "CHF", "SEK", "NOK", "CAD", "AUD"],
          "boc": ["USD", "EUR", "GBP", "JPY", "CHF", "AUD", "NZD", "CNY"]}
SOURCES = {
    "ecb": "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip",
    "boc": "https://www.bankofcanada.ca/valet/observations/" +
           ",".join("FX" + c + "CAD" for c in PANELS["boc"]) +
           "/json?start_date=2017-01-01&end_date=2025-12-31",
}
TERMS = {"ecb": "https://www.ecb.europa.eu/services/using-our-site/disclaimer/html/index.en.html",
         "boc": "https://www.bankofcanada.ca/terms/"}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    tmp.replace(path)


def easter(year):
    """Gregorian computus (calendar only)."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    n = h + l - 7 * m + 114
    return dt.date(year, n // 31, n % 31 + 1)


def holiday_candidates(source, year):
    """Recognized calendar closures; never delete an actually published row.

    BoC rules match national/bank schedule, not every provincial holiday.
    Unknown absent weekdays remain unresolved and invalidate the spanning return.
    """
    e = easter(year)
    fixed = lambda m, d: dt.date(year, m, d)
    if source == "ecb":
        days = {fixed(1, 1): "New Year", fixed(12, 25): "Christmas"}
        if year >= 2000:
            days.update({e - dt.timedelta(days=2): "Good Friday", e + dt.timedelta(days=1): "Easter Monday",
                         fixed(5, 1): "Labour Day", fixed(12, 26): "26 December"})
        if year in (1999, 2001):
            days[fixed(12, 31)] = "Special TARGET closure"
        return days
    def observed(x):
        return x + dt.timedelta(days=7 - x.weekday()) if x.weekday() >= 5 else x
    def monday(m, nth=1):
        x = fixed(m, 1)
        return x + dt.timedelta(days=(0 - x.weekday()) % 7 + 7 * (nth - 1))
    days = {observed(fixed(1, 1)): "New Year", monday(2, 3): "Family Day",
            e - dt.timedelta(days=2): "Good Friday", e + dt.timedelta(days=1): "Easter Monday",
            fixed(5, 24) - dt.timedelta(days=fixed(5, 24).weekday()): "Victoria Day",
            observed(fixed(7, 1)): "Canada Day", monday(8): "Civic Holiday",
            monday(9): "Labour Day", monday(10, 2): "Thanksgiving",
            observed(fixed(11, 11)): "Remembrance Day"}
    # Christmas and Boxing Day substitutes cannot collide.
    used = set()
    for m, d, label in [(12, 25, "Christmas"), (12, 26, "Boxing Day")]:
        x = fixed(m, d)
        while x.weekday() >= 5 or x in used:
            x += dt.timedelta(days=1)
        days[x] = label
        used.add(x)
    if year >= 2021:
        days[observed(fixed(9, 30))] = "Truth and Reconciliation"
    return days


def parse(raw, source, cutoff="2025-12-31"):
    cols = PANELS[source]
    if source == "ecb":
        if raw[:4] != b"PK\x03\x04":
            raise ValueError("ECB response is not a ZIP; HTML or other response rejected")
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            if z.testzip() is not None:
                raise ValueError("ZIP CRC failure")
            names = [n for n in z.namelist() if n.endswith(".csv")]
            if names != ["eurofxref-hist.csv"]:
                raise ValueError("Unexpected ECB archive members")
            reader = csv.DictReader(io.StringIO(z.read(names[0]).decode("utf-8-sig")), skipinitialspace=True)
            if not set(["Date"] + cols) <= set(reader.fieldnames or []):
                raise ValueError("ECB schema missing panel")
            records = [(r["Date"], [r.get(c) for c in cols]) for r in reader]
    else:
        obj = json.loads(raw)
        series = ["FX" + c + "CAD" for c in cols]
        if not set(series) <= set(obj.get("seriesDetail", {})) or "observations" not in obj:
            raise ValueError("BoC schema missing declared series")
        records = [(r["d"], [r.get(c, {}).get("v") for c in series]) for r in obj["observations"]]
    seen, points, incomplete = set(), [], []
    for date, values in records:
        dt.date.fromisoformat(date)
        if date in seen:
            raise ValueError("Duplicate observation date: " + date)
        seen.add(date)
        if date > cutoff:
            continue
        try:
            vals = [float(v) for v in values]
            valid = all(math.isfinite(v) and v > 0 for v in vals)
        except (TypeError, ValueError):
            valid = False
        if not valid:
            incomplete.append(date)
            continue
        points.append((date, [1 / v for v in vals] if source == "ecb" else vals))
    points.sort()
    if len(points) < 2:
        raise ValueError("Insufficient complete observations")
    observed = {dt.date.fromisoformat(x) for x in seen if x <= cutoff}
    first, last = map(dt.date.fromisoformat, (points[0][0], points[-1][0]))
    closures, unknown = {}, []
    calendars = {y: holiday_candidates(source, y) for y in range(first.year, last.year + 1)}
    for n in range((last - first).days + 1):
        day = first + dt.timedelta(days=n)
        if day.weekday() < 5 and day not in observed:
            if day in calendars[day.year]:
                closures[str(day)] = calendars[day.year][day]
            else:
                unknown.append(str(day))
    return points, {"raw_observations": len(records), "raw_first": min(seen), "raw_last": max(seen),
                    "after_cutoff": sum(d > cutoff for d in seen), "complete_levels": len(points),
                    "incomplete_dates": sorted(incomplete), "duplicate_dates": 0,
                    "recognized_missing_weekdays": closures, "unresolved_missing_weekdays": unknown}


def session_returns(dates, levels, blocked_dates):
    """No bridging incomplete or unexplained weekdays; weekends/known closures allowed."""
    r = 100 * (levels[1:] / levels[:-1] - 1)
    valid = np.array([not any(a < b < c for b in blocked_dates) for a, c in zip(dates[:-1], dates[1:])])
    return r, valid


def prepare(source, out, raw_file=None, cutoff="2025-12-31"):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rawpath = out / ("official_ecb.zip" if source == "ecb" else "official_boc.json")
    receipt = out / "retrieval.json"
    if raw_file is not None:
        supplied = Path(raw_file).read_bytes()
        if rawpath.exists() and rawpath.read_bytes() != supplied:
            raise ValueError("Refuse overwrite of different raw bytes")
        if not rawpath.exists():
            rawpath.write_bytes(supplied)
    elif not rawpath.exists():
        part = rawpath.with_suffix(rawpath.suffix + ".part")
        subprocess.run(["curl", "--fail", "--show-error", "--silent", "--location", "--retry", "2",
                        "--max-time", "60", "--dump-header", str(out / "download.headers"),
                        "--output", str(part), SOURCES[source]], check=True)
        parse(part.read_bytes(), source, cutoff)  # Validate before accepting download.
        part.replace(rawpath)
    raw = rawpath.read_bytes()
    headers = (out / "download.headers").read_text() if (out / "download.headers").exists() else ""
    if headers:
        mime = "application/zip" if source == "ecb" else "application/json"
        if mime not in headers.lower():
            raise ValueError("Unexpected HTTP content type")
    if not receipt.exists():
        # Initial manually downloaded curl bytes have the local completed-file timestamp.
        atomic_json(receipt, {"retrieved_utc": dt.datetime.fromtimestamp(rawpath.stat().st_mtime, dt.timezone.utc).isoformat(),
                              "url": SOURCES[source], "http_headers": headers, "raw_sha256": sha256(rawpath)})
    retrieval = json.loads(receipt.read_text())
    if retrieval["raw_sha256"] != sha256(rawpath):
        raise ValueError("Immutable raw checksum changed")
    points, audit = parse(raw, source, cutoff)
    dates = [d for d, _ in points]
    levels = np.array([x for _, x in points])
    blocked = sorted(set(audit["incomplete_dates"] + audit["unresolved_missing_weekdays"]))
    _, eligible = session_returns(dates, levels, blocked)
    buf = io.StringIO(newline="")
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["date"] + PANELS[source])
    writer.writerows(points_row for date, x in points for points_row in [[date] + x])
    levelspath = out / "levels.csv"
    text = buf.getvalue()
    if levelspath.exists() and levelspath.read_text() != text:
        raise ValueError("Refuse changed derived panel in same dataset directory")
    levelspath.write_text(text)
    manifest = {"schema_version": 1, "source": source, "url": SOURCES[source], **retrieval,
                "raw_size_bytes": len(raw), "cutoff": cutoff, "first": dates[0], "last": dates[-1],
                "columns": PANELS[source], "base": "EUR" if source == "ecb" else "CAD",
                "terms_url": TERMS[source], "terms_checked_utc_date": "2026-10-05",
                "use_gate": "academic analysis/aggregate publication with attribution, accuracy and modification disclosure; no raw redistribution here",
                "quote_original": "foreign currency per EUR" if source == "ecb" else "CAD per foreign currency",
                "transformation": "ECB reciprocal; BoC unchanged; simple level ratios times 100; no fill",
                "publication_schedule": "~14:30 CET before 2016-07-01, ~16:00 CET after" if source == "ecb" else "business day by 16:30 America/Toronto; delays possible",
                "assumed_available_time": "observation date 23:59:59 UTC; additional full observation gap; not actual historical release logs",
                "vintage": "latest downloaded retrospective vintage; historical revisions/publication delays not reconstructed",
                "levels_sha256": sha256(levelspath), **audit, "blocked_dates": blocked,
                "candidate_returns": len(eligible), "valid_returns": int(eligible.sum()),
                "excluded_spanning_returns": [dates[i + 1] for i in range(len(eligible)) if not eligible[i]],
                "gap_rule": "invalid if spanning incomplete date or unrecognized absent weekday; recognized closure/weekend remains one reference session, not one calendar day"}
    atomic_json(out / "manifest.json", manifest)
    return manifest


def load_panel(directory):
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text())
    if sha256(directory / "levels.csv") != manifest["levels_sha256"]:
        raise ValueError("Derived data checksum mismatch")
    with (directory / "levels.csv").open() as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != ["date"] + PANELS[manifest["source"]]:
            raise ValueError("Risk-factor order mismatch")
        rows = list(reader)
    dates = [r["date"] for r in rows]
    if dates != sorted(set(dates)):
        raise ValueError("Unsorted/duplicate panel")
    x = np.array([[float(r[c]) for c in manifest["columns"]] for r in rows])
    if not np.isfinite(x).all() or (x <= 0).any():
        raise ValueError("Invalid positive level panel")
    returns, valid = session_returns(dates, x, manifest["blocked_dates"])
    return dates, returns, valid, manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", choices=PANELS, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--raw-file", type=Path)
    args = p.parse_args()
    print(json.dumps(prepare(args.source, args.out, args.raw_file), indent=2))


if __name__ == "__main__":
    main()
