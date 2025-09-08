#!/usr/bin/env python3
import subprocess

# ----------------------------
# Configuration
# ----------------------------
AD_GROUP = "custom_scan_users"
TSV_FILE = "../exports/users.txt"
DEST_IP = "192.168.50.51"
PRINTER_USER = "printer_smb_user"
PRINTER_PASS = "SuperSecretPassword"   # replace with the real password

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
# Step 2: Read TSV as UTF-16 LE
# ----------------------------
with open(TSV_FILE, "rb") as f:
    raw_data = f.read()

text = raw_data.decode("utf-16-le", errors="ignore")
lines = text.splitlines()

# ----------------------------
# Step 3: Find header and metadata
# ----------------------------
header_line = None
for i, line in enumerate(lines):
    if line.startswith("AbbrNo\t") or line.startswith("Name\t"):
        header_line = i
        break

if header_line is None:
    raise ValueError("Could not find header line in TSV")

metadata_lines = lines[:header_line]   # keep @Ver688, #Abbreviate etc.
header = lines[header_line].split("\t")

# ----------------------------
# Step 3b: Debug print of columns
# ----------------------------
print("📑 Columns found in TSV:", header)

data_lines = lines[header_line+1:]

# ----------------------------
# Step 4: Column indices
# ----------------------------
abbrno_idx = header.index("AbbrNo")
name_idx = header.index("Name")
sendmode_idx = header.index("SendMode")
smbaddress_idx = header.index("SMBAddress")
smbfolder_idx = header.index("SMBFolder")
smblogin_idx = header.index("SMBLoginUser")
smbpass_idx = header.index("SMBLoginPassword")
searchkey_idx = header.index("SearchKey")

# Updated mapping for Group/Level
group_idx = header.index("ReferGroupNo")         # maps to "Group"
level_idx = header.index("ReferPossibleLevel")   # maps to "Level"

# ----------------------------
# Step 5: Parse rows
# ----------------------------
smb_rows = {}   # username -> row
other_rows = []

for row in data_lines:
    if row.startswith("@End") or not row.strip():
        continue
    cols = row.split("\t")

    # Ensure row has enough columns
    if len(cols) < len(header):
        cols += [""] * (len(header) - len(cols))

    sendmode = cols[sendmode_idx].strip() if sendmode_idx < len(cols) else ""
    if sendmode == "Smb":
        username = cols[name_idx].strip()
        if username:
            smb_rows[username] = cols
    else:
        other_rows.append(cols)

# ----------------------------
# Step 6: Remove SMB users not in AD
# ----------------------------
smb_rows = {u: r for u, r in smb_rows.items() if u in ad_users}

# ----------------------------
# Step 7: Add / update AD users as SMB (unique AbbrNo across all rows)
# ----------------------------

# Step 7a: Collect all existing AbbrNo from every row
used_abbrnos = set()

for row in other_rows + list(smb_rows.values()):
    try:
        if row[abbrno_idx].isdigit():
            used_abbrnos.add(int(row[abbrno_idx]))
    except IndexError:
        pass

# Function to get the next unique AbbrNo
next_abbrno = 1
def get_next_abbrno():
    global next_abbrno
    while next_abbrno in used_abbrnos:
        next_abbrno += 1
    used_abbrnos.add(next_abbrno)
    return next_abbrno

# Step 7b: Add / update SMB users
for user in ad_users:
    if user in smb_rows:
        row = smb_rows[user]
    else:
        row = [""] * len(header)

    # Ensure row is padded
    if len(row) < len(header):
        row += [""] * (len(header) - len(row))

    # Core SMB fields
    row[name_idx] = user
    row[sendmode_idx] = "Smb"
    row[smbaddress_idx] = DEST_IP
    row[smbfolder_idx] = user
    row[smblogin_idx] = PRINTER_USER
    row[smbpass_idx] = PRINTER_PASS

    # Fill AbbrNo uniquely across all rows
    if not row[abbrno_idx].isdigit() or int(row[abbrno_idx]) in used_abbrnos:
        row[abbrno_idx] = str(get_next_abbrno())

    # Fill Group/Level/SearchKey
    row[group_idx] = "0"
    row[level_idx] = "0"
    row[searchkey_idx] = user.lower()

    smb_rows[user] = row


# ----------------------------
# Step 8: Combine rows
# ----------------------------
final_rows = other_rows + list(smb_rows.values())
final_lines = metadata_lines + ["\t".join(header)] + ["\t".join(r) for r in final_rows] + ["@End"]

# ----------------------------
# Step 9: Save back as UTF-16 LE
# ----------------------------
with open(TSV_FILE, "wb") as f:
    f.write("\n".join(final_lines).encode("utf-16-le"))

print("✅ TSV updated successfully with AD SMB users.")
