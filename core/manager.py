from core.printer import Printer
import os
from utils.get_smb_ids import get_smb_ids

class PrinterManager:
    """Handles multiple printers."""

    def __init__(self, printer_configs):
        """
        printer_configs: list of dicts with keys: ip, username (optional)
        """
        self.printers = [
            Printer(ip=p["ip"], username=p.get("username"), password=p.get("password"))
            for p in printer_configs
        ]

    def login_all(self, default_username=None, default_password=None):
        """Attempt login on all printers. Returns dict of ip -> success bool."""
        results = {}
        for printer in self.printers:
            success = printer.login(username=default_username, password=default_password)
            results[printer.ip] = success
        return results

    def logout_all(self):
        results = {}
        for printer in self.printers:
            success = printer.logout()
            results[printer.ip] = success
        return results

    def export_all_address_books(self, out_dir="exports"):
        """Export address books from all printers following the correct workflow"""
        import os
        os.makedirs(out_dir, exist_ok=True)

        for printer in self.printers:
            print(f"📡 Exporting address book from {printer.ip}...")

            try:
                # Step 1: Request export
                if not printer.request_address_book_export():
                    print(f"❌ Failed to request export on {printer.ip}")
                    continue

                # Step 2: Poll until ready
                if not printer.poll_for_job_completion(job_type="export"):
                    print(f"❌ Export did not complete for {printer.ip}")
                    continue

                # Step 3: Get download token
                token = printer.get_download_token()
                if not token:
                    print(f"❌ No download token from {printer.ip}")
                    continue

                # Step 4: Download file
                file_path = f"{out_dir}/address_book_{printer.ip}.txt"
                if printer.download_address_book(token, file_path):
                    print(f"✅ Saved: {file_path}")
                else:
                    print(f"❌ Failed to download from {printer.ip}")

            except Exception as e:
                print(f"[ERROR] {printer.ip}: {e}")


    def import_all_address_books(self):
        """Import address books to all printers following the correct workflow"""

        for printer in self.printers:
            print(f"📡 Importing address book to {printer.ip}...")

            try:
                # Step 1: Request import
                if not printer.request_address_book_import():
                    print(f"❌ Failed to request import on {printer.ip}")
                    continue

                # Step 2: Poll until ready
                if not printer.poll_for_job_completion(job_type="import", interval=5):
                    print(f"❌ Import did not complete for {printer.ip}")
                    continue

            except Exception as e:
                print(f"[ERROR] {printer.ip}: {e}")
                
    def delete_smb_items(self):
        """Delete existing smb items from printer, """
        for printer in self.printers:
            
            ids = get_smb_ids(printer.ip)
            for item_id in ids :
                printer.delete_address_item(item_id)
            
            print(f"✅ Deleted smb items for printer: {printer.ip}")
                
        
            
            