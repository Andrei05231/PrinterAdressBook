import requests
import pickle
import os
import json
import copy
from utils.http import make_request, send_custom_request, check_response
import time 
from config.settings import BROWSER_COOKIES,LOGIN_PAYLOAD, EXPORT_PAYLOAD, IMPORT_PAYLOAD, SMB_IP, SMB_USER, SMB_BOOK_PATH


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
    
    def reset_session(self):
        """Delete everything related to the current session."""
        filename = os.path.join(self.SESSION_FILE, f"{self.ip}.cookies")
        
        # Delete the saved cookie file if it exists
        if os.path.exists(filename):
            os.remove(filename)
            print(f"[INFO] Session deleted for printer {self.ip}")
        
        # Clear the in-memory session
        self.session = None

    def login(self, username=None, password=None):
        """Log in to the printer as admin. Returns True if successful."""
        self.username = username or self.username
        self.password = password or self.password
        if not self.username or not self.password:
            print(f"[WARN] Missing credentials for printer {self.ip}")
            return False

        self.session = requests.Session()

        login_url = f"http://{self.ip}/wcd/login.cgi"

        # Browser-mimicking payload (imported and filled in)
        payload = copy.deepcopy(LOGIN_PAYLOAD)
        payload["username"] = self.username
        payload["password"] = self.password

        # Optional headers if needed
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = make_request(self.session, login_url, data=payload, headers=headers)

        if response and response.ok:
            try:
                status = check_response(response.content)
                if status == "200":
                    self.save_session()
                    print(f"[INFO] Admin login successful for {self.ip}")
                    return True
                else:
                    print(f"[WARN] Login failed for {self.ip} due to {status}")
                    return False

                
            except Exception as e :
                print(f"[WARN] Login request failed for {self.ip} due to {e}")
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
            try:
                status = check_response(response.content)
                if status == "200":
                    print(f"[INFO] Admin logout successful for {self.ip}")
                    self.reset_session()
                    return True
                else:
                    print(f"[WARN] Logout failed for {self.ip} due to {status}")
                    return False

            except Exception as e :
                print(f"[WARN] Logout request failed for {self.ip} due to {e}")
                return False

        print(f"[WARN] Logout failed for {self.ip}")
        return False

    def request_address_book_export(self) -> bool:
        """Request address book export - returns True if export started successfully"""
        if not self.load_session():
            print(f"[WARN] No session for {self.ip}")
            return False

        if not self.h_token:
            self.h_token = self._get_current_token()

        payload = copy.deepcopy(EXPORT_PAYLOAD)

        return send_custom_request(
            self.session,
            self.ip,
            self.h_token,
            "_000_002_IMP007",
            payload,
            "DeviceExportExec"
        )


    def request_address_book_import(self) -> bool:
        url = f"http://{self.ip}/wcd/api/AppReqSetCustomMessage/_000_002_IMP008"

        if not self.load_session():
            print(f"[WARN] No session for {self.ip}")
            return False
        if not self.h_token:
            self.h_token = self._get_current_token()

        headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-encoding": "gzip, deflate",
            "accept-language": "en-US,en;q=0.9",
            "connection": "keep-alive",
            "host": self.ip,
            "origin": f"http://{self.ip}",
            "referer": f"http://{self.ip}/wcd/spa_contents_frame.tmpl.html",
        }

        data = {
            "func": "PSL_AS_ADD_ADD",
            "h_token": self.h_token,
            "AS_ADD_H_BUT": "Import",
            "AS_ADD_H_DUM": "",
            "AS_ADD_T_PSS": "",
            "AS_ADD_R_IMP": "AddrImportType1",
            "SMB_H_CHOOSE_TYPE": "",
            "SMB_H_HOST_NAME": "",
            "SMB_H_USER_NAME": "",
            "SMB_H_FILE_PATH": "",
            "SMB_H_FILE_TITLE": "",
            "AS_ADD_IMP_R_SEL": "IndividualAbbrev",
            "AS_ADD_R_TYPE": "",
        }

        files = {
            "AS_ADD_F_FIL": open(f"exports/address_book_{self.ip}.txt", "rb")
        }

        response = self.session.post(url, headers=headers, data=data, files=files)

        return response


    def poll_for_job_completion(self, job_type="export", interval=5, max_attempts=12) -> bool:
        progress_url = f"http://{self.ip}/wcd/progress"

        for attempt in range(max_attempts):
            time.sleep(interval)
            print(f"[INFO] Checking {job_type} progress for {self.ip} (attempt {attempt + 1})")

            try:
                response = make_request(self.session, progress_url, data={})
                if not response:
                    continue

                data = response.json()
                mfp = data.get("MFP", {})

                message = mfp.get("Message")

                message_code = None
                message_text = None

                # Safely handle Message being a dict or list or None
                if isinstance(message, dict):
                    message_code = message.get("Item", {}).get("@Code")
                    message_text = message.get("Item", {}).get("#text")
                elif isinstance(message, list) and len(message) > 0 and isinstance(message[0], dict):
                    message_code = message[0].get("Item", {}).get("@Code")
                    message_text = message[0].get("Item", {}).get("#text")
                # else: message_code/message_text remain None

                # --- Export ---
                if job_type == "export":
                    if message_code == "Ok_1" and message_text == "ReadyToDownload":
                        print(f"[INFO] Export ready for download on {self.ip}")
                        return True
                    elif message_code == "DeviceExportExec":
                        continue

                # --- Import ---
                elif job_type == "import":
                    if message_code == "Ok_1":
                        print(f"[INFO] Import completed successfully on {self.ip}")
                        return True
                    elif message_code == "DeviceImportExec":
                        continue
                    elif mfp.get("RedirectUrl") == "progress":
                        # Job started, keep polling
                        continue

            except Exception as e:
                print(f"[WARN] Could not check {job_type} progress: {e}")
                continue

        print(f"[WARN] {job_type.capitalize()} did not complete within timeout for {self.ip}")
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
        
    def delete_address_item(self, item_id):
        url = f"http://{self.ip}/wcd/api/AppReqSetCustomMessage/_007_000_ABR000"
        
        if not self.load_session():
            print(f"[WARN] No session for {self.ip}")
            return False
        if not self.h_token:
            self.h_token = self._get_current_token()
        
        params = {
            "func":"PSL_AC_ABR_DEL",
            "h_token":self.h_token,
            "AC_ABR_H_NUM":item_id,
            "AC_ABR_H_AKI":"Public",
            "AC_ABR_H_FAV":""
        }
        
        response = make_request(self.session, url, params=params)
        
            
