import requests
import pickle
import os
from utils.http import make_request

class Printer:
    """Handles single printer operations."""

    def __init__(self, ip, username=None, password=None):
        self.ip = ip
        self.username = username
        self.password = password
        self.session = None

    SESSION_FILE = "sessions"  # folder to store session files

    def save_session(self):
        if not self.session:
            return
        os.makedirs(self.SESSION_FILE, exist_ok=True)
        filename = os.path.join(self.SESSION_FILE, f"{self.ip}.cookies")
        with open(filename, "wb") as f:
            pickle.dump(self.session.cookies, f)
        print(f"[INFO] Session saved for printer {self.ip}")

    def load_session(self):
        filename = os.path.join(self.SESSION_FILE, f"{self.ip}.cookies")
        if not os.path.exists(filename):
            return False
        self.session = requests.Session()
        with open(filename, "rb") as f:
            self.session.cookies.update(pickle.load(f))
        return True

    def login(self, username=None, password=None):
        """Log in to the printer as admin. Returns True if successful."""
        self.username = username or self.username
        self.password = password or self.password
        if not self.username or not self.password:
            print(f"[WARN] Missing credentials for printer {self.ip}")
            return False

        self.session = requests.Session()

        login_url = f"http://{self.ip}/wcd/login.cgi"

        # Browser-mimicking payload
        payload = {
            "func": "PSL_LP1_LOG",
            "AuthType": "None",
            "TrackType": "",
            "ExtSvType": "0",
            "PswcForm": "",
            "Mode": "",
            "publicuser": "",
            "username": self.username,
            "password": self.password,
            "AuthorityType": "",
            "R_ADM": "AdminAdmin",
            "ExtServ": "0",
            "ViewMode": "",
            "BrowserMode": "",
            "Lang": "",
            "trackname": "",
            "trackpassword": ""
        }

        # Optional headers if needed
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = make_request(self.session, login_url, data=payload, headers=headers)
        if response and response.ok:
            print(f"[INFO] Admin login successful for {self.ip}")
            self.save_session()
            return True
        print(f"[WARN] Login failed for {self.ip}")
        return False

    def get_status(self):
        """Get printer status."""
        if not self.session:
            print(f"[WARN] Not logged in: {self.ip}")
            return None

        status_url = f"http://{self.ip}/status"  # Placeholder
        response = make_request(self.session, status_url)
        if response:
            return response.text
        return None

    def logout(self):
        """Log out from the printer admin session."""

        if not self.load_session():
            print(f"[WARN] No saved session for printer {self.ip}")
            return False

        logout_url = f"http://{self.ip}/wcd/a_user.cgi"
        payload = {
            "func": "PSL_ACO_LGO",
            "h_token":  ""
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        response = make_request(self.session, logout_url, data=payload, headers=headers)
        if response and response.ok:
            print(f"[INFO] Admin logout successful for {self.ip}")
            self.session = None
            return True

        print(f"[WARN] Logout failed for {self.ip}")
        return False
