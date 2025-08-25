from core.printer import Printer

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
