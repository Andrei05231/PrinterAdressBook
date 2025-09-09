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
    """Send an import/export request to the MFP and check for expected response code."""
    if not h_token:
        print(f"[WARN] No h_token available for {ip}")
        return False

    import copy, json
    payload = copy.deepcopy(payload)
    payload["h_token"] = h_token

    url = f"http://{ip}/wcd/api/AppReqSetCustomMessage/{url_path}"
    headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

    response = make_request(session, url, data=json.dumps(payload), headers=headers)
    if not response:
        return False

    try:
        data = response.json()
        mfp = data.get("MFP", {})

        # --- Case 1: normal export/import response with message code ---
        message = mfp.get("Message")
        message_code = None
        if isinstance(message, dict):
            message_code = message.get("Item", {}).get("@Code")

        if message_code == expected_code:
            print(f"[INFO] Request '{expected_code}' started for {ip}")
            return True

        # --- Case 2: import "progress" redirect ---
        if mfp.get("RedirectUrl") == "progress":
            print(f"[INFO] Import started (redirected to progress) for {ip}")
            return True

        # --- Fallback: unexpected ---
        print(f"[WARN] Unexpected response from {ip}: {data}")
        return False

    except Exception as e:
        print(f"[ERROR] Could not parse response from {ip}: {e}")
        return False
