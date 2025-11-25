"""File-backed report CRUD helpers.

This module provides simple create/read/update/delete helpers that operate
on the existing JSON-lines files under `reports/` so the rest of the app can
use a single API instead of duplicating file logic in pages.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

REPORTS_DIR = "reports"
REPORTS_PATH = os.path.join(REPORTS_DIR, "reports.jsonl")
RESOLVED_PATH = os.path.join(REPORTS_DIR, "resolved_reports.jsonl")


def _ensure_dir():
    os.makedirs(REPORTS_DIR, exist_ok=True)


def _read_all() -> List[Dict[str, Any]]:
    reports: List[Dict[str, Any]] = []
    if not os.path.exists(REPORTS_PATH):
        return reports
    with open(REPORTS_PATH, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                reports.append(obj)
            except Exception:
                # ignore malformed lines
                continue
    return reports


def _write_all(reports: List[Dict[str, Any]]) -> None:
    _ensure_dir()
    with open(REPORTS_PATH, "w", encoding="utf-8") as fh:
        for r in reports:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def create_report(listing_id: int, reporter_id: Optional[int], reason: str = "") -> Dict[str, Any]:
    """Create a new report. Prevent duplicate reports from same reporter on same listing.

    Returns a dict with either {"status":"ok","report":...} or
    {"status":"duplicate","existing":...}
    """
    _ensure_dir()
    report = {
        "id": str(uuid4()),
        "listing_id": int(listing_id),
        "reporter_id": int(reporter_id) if reporter_id is not None else None,
        "reason": (reason or "").strip(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    # check duplicates
    try:
        existing = _read_all()
        for ex in existing:
            try:
                if (
                    ex.get("listing_id") == int(listing_id)
                    and ex.get("reporter_id")
                    == (int(reporter_id) if reporter_id is not None else None)
                ):
                    return {"status": "duplicate", "existing": ex}
    except Exception:
        # if reading fails, continue to append to preserve user report
        pass

    with open(REPORTS_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(report, ensure_ascii=False) + "\n")
    return {"status": "ok", "report": report}


def list_open_reports() -> List[Dict[str, Any]]:
    """Return all open (unresolved) reports as a list."""
    return _read_all()


def get_report(report_id: str) -> Optional[Dict[str, Any]]:
    for r in _read_all():
        if r.get("id") == report_id:
            return r
    return None


def resolve_report(report_id: str, resolver: str, resolution: str = "resolved") -> bool:
    """Mark the given report as resolved and move it to the resolved file.

    Returns True if the report was found and moved, False otherwise.
    """
    reports = _read_all()
    for i, r in enumerate(reports):
        if r.get("id") == report_id:
            rep_res = r.copy()
            rep_res["resolved_by"] = resolver
            rep_res["resolved_at"] = datetime.utcnow().isoformat() + "Z"
            rep_res["resolution"] = resolution
            os.makedirs(REPORTS_DIR, exist_ok=True)
            with open(RESOLVED_PATH, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rep_res, ensure_ascii=False) + "\n")
            reports.pop(i)
            _write_all(reports)
            return True
    return False


def delete_report(report_id: str) -> bool:
    """Delete an open report (without writing to resolved). Returns True if removed."""
    reports = _read_all()
    for i, r in enumerate(reports):
        if r.get("id") == report_id:
            reports.pop(i)
            _write_all(reports)
            return True
    return False
