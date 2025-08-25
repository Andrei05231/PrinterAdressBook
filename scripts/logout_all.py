from config.printers import PRINTERS
from config.settings import ADMIN_USER, ADMIN_PASS
from core.manager import PrinterManager

def main():
    manager = PrinterManager(PRINTERS)
    results = manager.logout_all()
    for ip, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {ip}")

if __name__ == "__main__":
    main()

