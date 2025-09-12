#!/usr/bin/env python3
import subprocess
from pathlib import Path
from config.settings import SMB_USER, SMB_PASS, SMB_IP

# ----------------------------
# Configuration
# ----------------------------
AD_GROUP = "custom_scan_users"
EXPORTS_FOLDER = Path("exports/")
DEST_IP = SMB_IP
PRINTER_USER = SMB_USER
PRINTER_PASS = fr"[CONV]{SMB_PASS}" 

# ----------------------------
# Step 1: Get AD users
# ----------------------------
try:
    output = subprocess.check_output(["wbinfo", "--group-info", AD_GROUP], text=True)
    ad_users = output.split(":")[3].strip().split(",") if ":" in output else []
    ad_users = [u.strip() for u in ad_users if u.strip()]
    print(f"AD users fetched: {ad_users}")
except subprocess.CalledProcessError:
    print(f"⚠️ Could not fetch users from AD group '{AD_GROUP}'.")
    ad_users = []

# ----------------------------
# Function to compute SearchKey
# ----------------------------
def compute_searchkey(name: str) -> str:
    first = name[:1].upper()
    mapping = [
        ("Abc", "ABC"),
        ("Def", "DEF"),
        ("Ghi", "GHI"),
        ("Jkl", "JKL"),
        ("Mno", "MNO"),
        ("Pqrs", "PQRS"),
        ("Tuv", "TUV"),
        ("Wxyz", "WXYZ")
    ]
    return next((key for key, letters in mapping if first in letters), "Other")

# ----------------------------
# Function to process a single TSV
# ----------------------------
def process_tsv(tsv_file: Path):
    print(f"\n📂 Processing file: {tsv_file}")
    with open(tsv_file, "rb") as f:
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
        print(f"⚠️ Could not find header in {tsv_file}, skipping...")
        return

    metadata_lines = lines[:header_line]
    header = lines[header_line].split("\t")
    data_lines = lines[header_line+1:]

    # Column indices
    abbrno_idx = header.index("AbbrNo")
    name_idx = header.index("Name")
    sendmode_idx = header.index("SendMode")
    smbaddress_idx = header.index("SMBAddress")
    smbfolder_idx = header.index("SMBFolder")
    smblogin_idx = header.index("SMBLoginUser")
    smbpass_idx = header.index("SMBLoginPassword")
    searchkey_idx = header.index("SearchKey")
    use_refer_licence_idx = header.index("UseReferLicence")
    group_idx = header.index("ReferGroupNo")
    level_idx = header.index("ReferPossibleLevel")
    welluse_idx = header.index("WellUse")
    pinyin_idx = header.index("Pinyin")

    # Parse rows
    smb_rows = {}
    other_rows = []
    for row in data_lines:
        if row.startswith("@End") or not row.strip():
            continue
        cols = row.split("\t")
        if len(cols) < len(header):
            cols += [""] * (len(header) - len(cols))
        sendmode = cols[sendmode_idx].strip() if sendmode_idx < len(cols) else ""
        if sendmode == "Smb":
            username = cols[name_idx].strip()
            if username:
                smb_rows[username] = cols
        else:
            other_rows.append(cols)

    # Remove SMB users not in AD
    smb_rows = {u: r for u, r in smb_rows.items() if u in ad_users}

    # Unique AbbrNo
    used_abbrnos = set()
    for row in other_rows + list(smb_rows.values()):
        try:
            if row[abbrno_idx].isdigit():
                used_abbrnos.add(int(row[abbrno_idx]))
        except IndexError:
            pass
    next_abbrno = 1
    def get_next_abbrno():
        nonlocal next_abbrno
        while next_abbrno in used_abbrnos:
            next_abbrno += 1
        used_abbrnos.add(next_abbrno)
        return next_abbrno

    # Add/update SMB users
    for user in ad_users:
        if user in smb_rows:
            row = smb_rows[user]
        else:
            row = [""] * len(header)
        if len(row) < len(header):
            row += [""] * (len(header) - len(row))
        row[name_idx] = user
        row[sendmode_idx] = "Smb"
        row[smbaddress_idx] = DEST_IP
        row[smbfolder_idx] = fr"\servicePath\{user}"
        row[smblogin_idx] = PRINTER_USER
        row[smbpass_idx] = PRINTER_PASS
        if not row[abbrno_idx].isdigit() or int(row[abbrno_idx]) in used_abbrnos:
            row[abbrno_idx] = str(get_next_abbrno())
        row[group_idx] = "0"
        row[level_idx] = "0"
        row[use_refer_licence_idx] = "Level"

        # New fields
        row[welluse_idx] = "No"
        row[pinyin_idx] = "No"

        # SearchKey logic
        row[searchkey_idx] = compute_searchkey(user)

        smb_rows[user] = row

    # Combine rows
    final_rows = other_rows + list(smb_rows.values())
    final_lines = metadata_lines + ["\t".join(header)] + ["\t".join(r) for r in final_rows] + ["@End"]

    # Save back
    with open(tsv_file, "wb") as f:
        f.write("\n".join(final_lines).encode("utf-16-le"))
    print(f"✅ {tsv_file} updated successfully.")

# ----------------------------
# Step 2: Process all files in exports folder
# ----------------------------
for file in EXPORTS_FOLDER.glob("*.txt"):
    process_tsv(file)
