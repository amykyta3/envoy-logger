import requests
import urllib3
from datetime import datetime, timezone
import logging
from typing import Dict

from . import model

# Local envoy access uses self-signed certificate. Ignore the warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LOG = logging.getLogger("envoy")


def login(url: str, token: str) -> str:
    """
    Login to local envoy and return the session id
    """
    headers = {
        "Authorization": f"Bearer {token}",
    }
    response = requests.get(
        f"{url}/auth/check_jwt",
        headers=headers,
        verify=False,
        timeout=30,
    )
    response.raise_for_status()  # raise HTTPError if one occurred
    session_id = response.cookies["sessionId"]
    LOG.info("Logged into envoy. SessionID: %s", session_id)
    return session_id


def get_power_data(url: str, session_id: str) -> model.SampleData:
    LOG.debug("Fetching power data")
    ts = datetime.now(timezone.utc)
    cookies = {
        "sessionId": session_id,
    }
    response = requests.get(
        f"{url}/production.json?details=1",
        cookies=cookies,
        verify=False,
        timeout=30,
    )
    response.raise_for_status()  # raise HTTPError if one occurred
    json_data = response.json()
    data = model.SampleData(json_data, ts)
    return data


def get_inverter_data(url: str, session_id: str) -> Dict[str, model.InverterSample]:
    LOG.debug("Fetching inverter data")
    ts = datetime.now(timezone.utc)
    cookies = {
        "sessionId": session_id,
    }
    response = requests.get(
        f"{url}/api/v1/production/inverters",
        cookies=cookies,
        verify=False,
        timeout=30,
    )
    response.raise_for_status()  # raise HTTPError if one occurred
    json_data = response.json()
    data = model.parse_inverter_data(json_data, ts)
    return data


def get_inventory(url: str, session_id: str):
    cookies = {
        "sessionId": session_id,
    }
    response = requests.get(
        f"{url}/inventory.json?deleted=1",
        cookies=cookies,
        verify=False,
        timeout=30,
    )
    response.raise_for_status()  # raise HTTPError if one occurred
    json_data = response.json()
    # TODO: Convert to objects
    return json_data
