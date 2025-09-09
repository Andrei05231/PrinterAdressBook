import requests
import json

def make_request(session, url, data=None, headers=None, params=None):
    try:
        if data:
            response = session.post(url, data=data, headers=headers, timeout=10)
        else:
            response = session.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"[ERROR] HTTP request failed: {e}")
        return None
    
def send_custom_request(session, ip, h_token, url_path: str, payload: dict, expected_code: str) -> bool:
    """
    Send a custom import/export request to the MFP and check for expected response code.

    Args:
        session: requests.Session object
        ip: device IP address
        h_token: security token for request
        url_path: API path, e.g. "_000_002_IMP007"
        payload: dict of request parameters (without h_token, it will be added)
        expected_code: expected response code string, e.g. "DeviceExportExec"

    Returns:
        True if the request was accepted, False otherwise
    """
    if not h_token:
        print(f"[WARN] No h_token available for {ip}")
        return False

    # Inject token into payload
    payload["h_token"] = h_token

    url = f"http://{ip}/wcd/api/AppReqSetCustomMessage/{url_path}"
    headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

    response = make_request(session, url, data=json.dumps(payload), headers=headers)
    if not response:
        return False

    try:
        data = response.json()
        message_code = data.get("MFP", {}).get("Message", {}).get("Item", {}).get("@Code")

        if message_code == expected_code:
            print(f"[INFO] Request '{expected_code}' started for {ip}")
            return True
        else:
            print(f"[WARN] Unexpected response from {ip}: {data}")
            return False
    except Exception as e:
        print(f"[ERROR] Could not parse response from {ip}: {e}")
        return False
