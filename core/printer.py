import requests
import pickle
import os
import json
from utils.http import make_request
import time 

class Printer:
    """Handles single printer operations."""

    def __init__(self, ip, username=None, password=None):
        self.ip = ip
        self.username = username
        self.password = password
        self.session = None
        self.h_token = ""

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
            data = pickle.load(f)
            self.session.cookies.update(data)
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
        testData = self.session.cookies.get_dict()
        print(f"response from login: {testData}")
        if response and response.ok:
            try:
                print(f"[INFO] Admin login successful for {self.ip}")
                self.save_session()
                return True
            except Exception:
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

    def request_address_book_export(self):
        self.load_session()
        url = f"http://{self.ip}/wcd/api/AppReqSetCustomMessage/_000_002_IMP007"
        payload = {
            "func": "PSL_AS_ADD_ADD",
            "h_token": "",
            "AS_ADD_H_BUT": "Export",
            "AS_AB_R_EX": "on",
            "AS_ADD_R_FILE_TYPE": "CSV",
            "AS_ADD_R_SEL": "Abbrev"
        }
        headers = {"Content-Type": "application/json"}

        response = make_request(self.session, url, data=json.dumps(payload), headers=headers)
        print(f"adress_book response: {response}")
        if not response:
            return False

        try:
            data = response.json()
            # sometimes the token is here, sometimes not
            token = data.get("MFP", {}).get("Token")
            if token:
                self.h_token = token
                return True

            # if not, poll progress
            return self.poll_for_export_token()

        except ValueError:
            # response wasn't JSON
            print(f"[ERROR] Non-JSON response from {self.ip}: {response.text}")
            return False

        except Exception as e:
            print(f"[ERROR] Could not parse export response: {e}")
            return False



    def poll_for_export_token(self, interval=5, max_attempts=10):
        progress_url = f"http://{self.ip}/wcd/progress"
        for attempt in range(max_attempts):
            time.sleep(interval)
            resp = make_request(self.session, progress_url)
            if not resp:
                continue
            try:
                data = resp.json()
                token = data.get("MFP", {}).get("Token")
                if token:
                    self.h_token = token
                    print(f"[INFO] Got export token for {self.ip}")
                    return True
            except:
                continue
        print(f"[WARN] Could not get export token for {self.ip}")
        return False

    def download_address_book(self, file_path="address_book.csv"):
        if not self.h_token:
            print(f"[WARN] No token available for {self.ip}")
            return False

        url = f"http://{self.ip}/wcd/a_filedownload"
        params = {
            "func": "PSL_AS_ADD_DLD",
            "h_token": self.h_token,
            "cginame1": "a_filedownload",
            "cginame2": "a_filedownload",
            "H_BAK": "0",
            "H_TAB": "",
            "H_DLV": ""
        }

        response = make_request(self.session, url, params=params)
        if response and response.ok:
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"[INFO] Address book downloaded for {self.ip}")
            return True
        return False

