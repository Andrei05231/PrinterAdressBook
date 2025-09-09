import requests
import pickle
import os
import json
from utils.http import make_request
import time 
from config.settings import BROWSER_COOKIES

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
        
        for name, value in BROWSER_COOKIES.items():
            self.session.cookies.set(name, value, domain=self.ip)

        with open(filename, "wb") as f:
            pickle.dump(self.session.cookies, f) 
        print(f"[INFO] Session saved for printer {self.ip}")

    def load_session(self):
        filename = os.path.join(self.SESSION_FILE, f"{self.ip}.cookies")
        if not os.path.exists(filename):
            return False
        self.session = requests.Session()
        with open(filename, "rb") as f:
            cookies = pickle.load(f)
            self.session.cookies.update(cookies)  
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
        
        self.save_session()
        testData = self.session.cookies.get_dict()
      
        if response and response.ok:
            try:
                print(f"[INFO] Admin login successful for {self.ip}")
                
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
        """Request address book export - returns True if export started successfully"""
        if not self.load_session():
            print(f"[WARN] No session for {self.ip}")
            return False
        
        # First, get the h_token from the page or session
        if not self.h_token:
            self.h_token = self._get_current_token()
        
        if not self.h_token:
            print(f"[WARN] No h_token available for {self.ip}")
            return False
        
        url = f"http://{self.ip}/wcd/api/AppReqSetCustomMessage/_000_002_IMP007"
        payload = {
            "func": "PSL_AS_ADD_ADD",
            "h_token": self.h_token,
            "AS_ADD_H_BUT": "Export",
            "AS_ADD_H_DUM": "",
            "AS_AB_R_EX": "on",
            "AS_ADD_R_FILE_TYPE": "CSV",
            "AS_ADD_T_PSS": "",
            "AS_ADD_R_SEL": "Abbrev",
            "AS_ADD_H_FILE_TYPE": "",
            "SMB_H_CHOOSE_TYPE": "",
            "SMB_H_HOST_NAME": "",
            "SMB_H_USER_NAME": "",
            "SMB_H_FILE_PATH": "",
            "SMB_H_FILE_TITLE": "",
            
        }
        
        # Send as JSON (as per your browser capture)
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        response = make_request(self.session, url, data=json.dumps(payload), headers=headers)
        
        if not response:
            return False
        
        try:
            data = response.json()
            # Check if export started (should show "DeviceExportExec")
            message_code = data.get("MFP", {}).get("Message", {}).get("Item", {}).get("@Code")
            if message_code == "DeviceExportExec":
                print(f"[INFO] Export started for {self.ip}")
                return True
            else:
                print(f"[WARN] Unexpected response from {self.ip}: {data}")
                return False
        except Exception as e:
            print(f"[ERROR] Could not parse export response from {self.ip}: {e}")
            return False

    def poll_for_export_completion(self, interval=5, max_attempts=12):
        """Poll progress until export is ready for download"""
        progress_url = f"http://{self.ip}/wcd/progress"
        
        for attempt in range(max_attempts):
            time.sleep(interval)
            print(f"[INFO] Checking export progress for {self.ip} (attempt {attempt + 1})")
            
            # POST to progress with no payload
            response = make_request(self.session, progress_url, data={})
            if not response:
                continue
            
            try:
                data = response.json()
                message_code = data.get("MFP", {}).get("Message", {}).get("Item", {}).get("@Code")
                message_text = data.get("MFP", {}).get("Message", {}).get("Item", {}).get("#text")
                
                if message_code == "Ok_1" and message_text == "ReadyToDownload":
                    print(f"[INFO] Export ready for download on {self.ip}")
                    return True
                elif message_code == "DeviceExportExec":
                    # Still processing, continue polling
                    continue
                else:
                    print(f"[WARN] Unexpected progress response from {self.ip}: {data}")
                    continue
                    
            except Exception as e:
                print(f"[ERROR] Could not parse progress response: {e}")
                continue
        
        print(f"[WARN] Export did not complete within timeout for {self.ip}")
        return False

    def get_download_token(self):
        """Get the download token after export is complete"""
        import time
        timestamp = int(time.time() * 1000)  # Current timestamp in milliseconds
        
        token_url = f"http://{self.ip}/wcd/api/AppReqGetCustomData/_000_002_IMP017?_={timestamp}"
        
        response = make_request(self.session, token_url)  # GET request, no data
        if not response:
            return None
        
        try:
            data = response.json()
            token = data.get("MFP", {}).get("Token")
            if token:
                print(f"[INFO] Got download token for {self.ip}")
                return token
            else:
                print(f"[WARN] No token in response from {self.ip}")
                return None
        except Exception as e:
            print(f"[ERROR] Could not parse token response: {e}")
            return None

    def download_address_book(self, token, file_path="address_book.txt"):
        """Download the address book using the token"""
        if not token:
            print(f"[WARN] No token available for {self.ip}")
            return False
        
        url = f"http://{self.ip}/wcd/a_filedownload"
        params = {
            "func": "PSL_AS_ADD_DLD",
            "h_token": token,
            "cginame1": "a_filedownload", 
            "cginame2": "a_filedownload",
            "H_BAK": "0",
            "H_TAB": "",
            "H_DLV": ""
        }
        
        # GET request with params
        response = make_request(self.session, url, params=params)
        if response and response.ok:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"[INFO] Address book downloaded to {file_path}")
            return True
        else:
            print(f"[WARN] Failed to download address book from {self.ip}")
            return False



    def _get_current_token(self):
        """Get the current h_token from the printer using the session cookies"""
        # Check if we even have a session cookie
        cookie_id = None
        for cookie in self.session.cookies:
            if cookie.name.upper() == 'ID' or 'ID' in cookie.name:  # Look for ID cookie
                cookie_id = cookie.value
                break

        if not cookie_id:
            print(f"[ERROR] No ID cookie found for {self.ip}")
            return ""

        # Generate a cache-busting timestamp in milliseconds
        timestamp = int(time.time() * 1000)

        token_url = f"http://{self.ip}/wcd/a_system_impexp.json?_={timestamp}"

        # Session will send cookies automatically
        response = make_request(self.session, token_url)  # GET request
        if not response:
            print(f"[ERROR] Could not get initial token from {self.ip}")
            return ""

        try:
            data = response.json()
            token = data.get("MFP", {}).get("Token")
            if token:
                print(f"[INFO] Got initial token for {self.ip}")
                return token
            else:
                print(f"[WARN] No token in initial response from {self.ip}")
                return ""
        except Exception as e:
            print(f"[ERROR] Could not parse initial token response: {e}")
            return ""
