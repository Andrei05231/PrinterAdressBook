from config.printers import PRINTERS
from core.manager import PrinterManager

if __name__ == "__main__":
    manager = PrinterManager(PRINTERS)
    manager.export_all_address_books()

