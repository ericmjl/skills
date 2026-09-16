# /// script
# dependencies = []
# ///
"""Upsert one entry into the Plaud sync state after a successful note write.

Usage:
    uv run upsert_state.py <plaud_id_bare> <plaud_name> <note_path> <recorded_at_iso> <duration_seconds>

- plaud_id_bare: file id WITHOUT the "of_" prefix (matches existing state keys).
- note_path: vault-relative path of the written note.
- recorded_at_iso: e.g. 2026-09-15T19:16:44-04:00, or the string null.
- duration_seconds: integer.

Sets source_updated_at: null (the Plaud list API exposes no updated field),
last_synced_at to now (America/New_York), status: synced, and computes
transcript_hash as sha256 of the note's "## Transcript" section body per
meta.hash_convention. Writes the state file atomically (temp file + rename).
Reads the state fresh at execution time; rerun per file, serially.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone

VAULT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
STATE_PATH = os.path.join(VAULT_ROOT, ".plaud", "state", "sync-state.json")

ET = timezone(timedelta(hours=-4))  # America/New_York, EDT (update for EST in winter)


def transcript_section_hash(note_path: str) -> str | None:
    """sha256 of the '## Transcript' section body of a note (whitespace-stripped)."""
    full = os.path.join(VAULT_ROOT, note_path)
    with open(full, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    start = None
    body: list[str] = []
    for line in lines:
        if line.strip() == "## Transcript":
            start = True
            continue
        if start:
            if line.startswith("## "):
                break
            body.append(line)
    if start is None:
        return None
    return hashlib.sha256("\n".join(body).strip().encode("utf-8")).hexdigest()


def main() -> int:
    if len(sys.argv) != 6:
        print(__doc__)
        return 2
    plaud_id, name, note_path, recorded_at, duration = sys.argv[1:6]
    if recorded_at == "null":
        recorded_at = None
    duration = int(duration)

    with open(STATE_PATH, encoding="utf-8") as fh:
        state = json.load(fh)

    state.setdefault("meta", {}).setdefault("field_names", {}).setdefault(
        "updated", None
    )
    state["meta"]["hash_convention"] = (
        "sha256 of the note file's '## Transcript' section body "
        "(lines between the '## Transcript' heading and the next '## ' heading "
        "or EOF, joined with newlines, whitespace-stripped)"
    )

    entry = state.setdefault("files", {}).get(plaud_id, {})
    entry.update(
        {
            "name": name,
            "note_path": note_path,
            "recorded_at": recorded_at,
            "source_updated_at": None,
            "transcript_hash": transcript_section_hash(note_path),
            "last_synced_at": datetime.now(ET).isoformat(timespec="seconds"),
            "status": "synced",
        }
    )
    if "duration_seconds" not in entry:
        entry["duration_seconds"] = duration
    state["files"][plaud_id] = entry

    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        dir=os.path.dirname(STATE_PATH), prefix=".sync-state-", suffix=".json"
    )
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, STATE_PATH)
    print(f"upserted {plaud_id} -> {note_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
