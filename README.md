# Konica Admin Tool

Automates Konica Bizhub address book synchronization with Active Directory users for SMB scan-to-folder functionality.

## What It Does

- Fetches users from AD group via `wbinfo`
- Exports address books from Konica printers (UTF-16LE TSV format)
- Updates with SMB entries: `\\SMB_IP\servicePath\{username}`
- Imports back to printers, preserving existing entries

## Setup

```bash
make venv && make install
```

Create `.env`:
```env
ADMIN_USER=printer_admin
ADMIN_PASS=admin_password
SMB_USER=smb_account
SMB_PASS=smb_password
SMB_IP=192.168.1.100
SMB_BOOK_PATH=\\server\scans
```

Configure printers in `config/printers.py`:
```python
PRINTERS = [{"ip": "192.168.1.10"}, {"ip": "192.168.1.11"}]
```

Set AD group in `scripts/update_address_book.py`:
```python
AD_GROUP = "scan_users"
```

## Usage

**Full sync:**
```bash
make run
```

**Individual steps:**
```bash
make login          # Authenticate to printers
make get_book       # Export address books  
make delete_smbs    # Remove existing SMB entries
make update_book    # Add AD users as SMB entries
make send_book      # Import back to printers
make logout         # Clean up sessions
```

## Technical Details

**Authentication:** HTTP session management with cookie persistence
**API Endpoints:** Uses Konica's web admin interface (`/wcd/` endpoints)
**File Format:** UTF-16LE encoded TSV with metadata headers
**Workflow:** Export → Process → Import with progress polling
**Session Storage:** Pickled cookies in `sessions/` directory

**Key Components:**
- `core/printer.py` - Individual printer HTTP operations
- `core/manager.py` - Multi-printer orchestration  
- `utils/http.py` - Request handling and response parsing
- `scripts/` - Executable modules for each operation

**Address Book Processing:**
- Parses TSV columns: `AbbrNo`, `Name`, `SendMode`, `SMBAddress`, etc.
- Generates SearchKey (A-Z categorization) 
- Assigns unique AbbrNo IDs
- Preserves non-SMB entries

## Requirements

- Python 3.6+, `wbinfo` (Samba client)
- Network access to printers and AD
- Admin credentials for Konica web interface
