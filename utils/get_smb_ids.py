#!/usr/bin/env python3
from pathlib import Path
import sys

def get_smb_ids(ip: str):
    filename = Path(f"exports/address_book_{ip}.txt")

    if not filename.exists():
        raise FileNotFoundError(f"File not found: {filename}")

    # Read the file as UTF-16LE
    with open(filename, "rb") as f:
        raw_data = f.read()
    text = raw_data.decode("utf-16-le", errors="ignore")
    lines = text.splitlines()

    # Find header
    header_line = None
    for i, line in enumerate(lines):
        if line.startswith("AbbrNo\t") or line.startswith("Name\t"):
            header_line = i
            break
    if header_line is None:
        raise ValueError(f"Could not find header in {filename}")

    header = lines[header_line].split("\t")
    data_lines = lines[header_line + 1 :]

    # Column indices
    abbrno_idx = header.index("AbbrNo")
    sendmode_idx = header.index("SendMode")

    # Collect AbbrNo values where SendMode == "Smb"
    abbrnos = []
    for row in data_lines:
        if row.startswith("@End") or not row.strip():
            continue
        cols = row.split("\t")
        if len(cols) <= max(abbrno_idx, sendmode_idx):
            continue
        if cols[sendmode_idx].strip() == "Smb":
            abbrnos.append(cols[abbrno_idx].strip())

    return abbrnos
