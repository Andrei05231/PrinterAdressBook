import requests

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