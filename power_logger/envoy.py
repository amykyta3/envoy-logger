import requests
import urllib3
from datetime import datetime, timezone
import logging
from typing import Dict

from . import model

# Local envoy access uses self-signed certificate. Ignore the warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LOG = logging.getLogger("envoy")

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
        verify=False,
        timeout=30,
    )
    response.raise_for_status() # raise HTTPError if one occurred
    session_id = response.cookies['sessionId']
    LOG.info("Logged into envoy. SessionID: %s", session_id)
    return session_id


def get_power_data(session_id: str) -> model.SampleData:
    LOG.info("Fetching power data")
    ts = datetime.now(timezone.utc)
    cookies = {
        'sessionId': session_id,
    }
    response = requests.get(
        'https://envoy.local/production.json?details=1',
        cookies=cookies,
        verify=False,
        timeout=30,
    )
    response.raise_for_status() # raise HTTPError if one occurred
    json_data = response.json()
    data = model.SampleData(json_data, ts)
    return data


def get_inverter_data(session_id: str) -> Dict[str, model.InverterSample]:
    LOG.info("Fetching inverter data")
    ts = datetime.now(timezone.utc)
    cookies = {
        'sessionId': session_id,
    }
    response = requests.get(
        'https://envoy.local/api/v1/production/inverters',
        cookies=cookies,
        verify=False,
        timeout=30,
    )
    response.raise_for_status() # raise HTTPError if one occurred
    json_data = response.json()
    data = model.parse_inverter_data(json_data, ts)
    return data


def get_inventory(session_id: str):
    cookies = {
        'sessionId': session_id,
    }
    response = requests.get(
        'https://envoy.local/inventory.json?deleted=1',
        cookies=cookies,
        verify=False,
        timeout=30,
    )
    response.raise_for_status() # raise HTTPError if one occurred
    json_data = response.json()
    # TODO: Convert to objects
    return json_data
