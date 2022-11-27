import requests
import urllib3
from datetime import datetime, timezone

from . import model

# Local envoy access uses self-signed certificate. Ignore the warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def login(token: str) -> str:
    """
    Login to local envoy and return the session id
    """
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.get(
        'https://envoy.local/auth/check_jwt',
        headers=headers,
        verify=False
    )
    response.raise_for_status() # raise HTTPError if one occurred
    return response.cookies['sessionId']


def get_power_data(session_id: str):
    ts = datetime.now(timezone.utc)
    cookies = {
        'sessionId': session_id,
    }
    response = requests.get(
        'https://envoy.local/production.json?details=1',
        cookies=cookies,
        verify=False
    )
    response.raise_for_status() # raise HTTPError if one occurred
    json_data = response.json()
    data = model.SampleData(json_data, ts)
    return data


def get_inventory(session_id: str):
    cookies = {
        'sessionId': session_id,
    }
    response = requests.get(
        'https://envoy.local/inventory.json?deleted=1',
        cookies=cookies,
        verify=False
    )
    response.raise_for_status() # raise HTTPError if one occurred
    json_data = response.json()
    # TODO: Convert to objects
    return json_data
