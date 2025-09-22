import requests
import json
import xml.etree.ElementTree as ET

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
        status = check_response(response.content)
        print(f"[WARN] Unexpected response from {ip}: {status}")
        return False

    except Exception as e:
        print(f"[ERROR] Could not parse response from {ip}: {e}")
        return False


def check_response(response_bytes: bytes) -> str:
    """
    Extracts error message from XML or JSON responses.
    Returns:
        - The <Item> text (XML) or JSON Item text if present.
        - "200" if response is neither XML nor JSON (assume success).
        - "ERROR" if something went wrong parsing known structures.
    """
    try:
        response_str = response_bytes.decode('utf-8', errors='ignore')

        # Try JSON first
        if response_str.strip().startswith('{'):
            data = json.loads(response_str)
            try:
                return data["MFP"]["Message"]["Item"]["#text"]
            except (KeyError, TypeError):
                return "ERROR"

        # Then try XML
        xml_start = response_str.find('<?xml')
        if xml_start != -1:
            xml_content = response_str[xml_start:]
            root = ET.fromstring(xml_content)
            item_tag = root.find('./Message/Item')
            if item_tag is not None:
                return item_tag.text
            return "ERROR"

        # Not XML or JSON → likely successful HTML/JS response
        return "200"

    except Exception:
        return "ERROR"
