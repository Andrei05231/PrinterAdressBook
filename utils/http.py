import requests

def make_request(session, url, data=None, headers=None):
    try:
        if data:
            response = session.post(url, data=data, headers=headers, timeout=5)
        else:
            response = session.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"[ERROR] HTTP request failed : {e}")
        return None
