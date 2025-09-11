from config.printers import PRINTERS
from config.settings import ADMIN_USER, ADMIN_PASS
from core.manager import PrinterManager

def main():
    manager = PrinterManager(PRINTERS)
    results = manager.delete_smb_items()

if __name__ == "__main__":
    main()

