from typing import Optional
from datetime import datetime, timedelta
import json
import base64
import os
import logging

import requests
from appdirs import user_cache_dir

LOG = logging.getLogger("enphaseenergy")


def _login_enphaseenergy(email: str, password: str) -> str:
    LOG.info("Logging into enphaseenergy.com as %s", email)
    # Login and get session ID
    files = {
        "user[email]": (None, email),
        "user[password]": (None, password),
    }
    url = "https://enlighten.enphaseenergy.com/login/login.json?"
    response = requests.post(
        url,
        files=files,
        timeout=30,
    )
    response.raise_for_status()  # raise HTTPError if one occurred
    resp = response.json()
    return resp["session_id"]


def get_new_token(email: str, password: str, envoy_serial: str) -> str:
    """
    Login to enphaseenergy.com and return an access token for the envoy.
    """
    session_id = _login_enphaseenergy(email, password)

    LOG.info("Downloading new access token for envoy S/N: %s", envoy_serial)
    # Get the token
    json_data = {
        "session_id": session_id,
        "serial_num": envoy_serial,
        "username": email,
    }
    response = requests.post(
        "https://entrez.enphaseenergy.com/tokens",
        json=json_data,
        timeout=30,
    )
    response.raise_for_status()  # raise HTTPError if one occurred
    return response.text


def token_expiration_date(token: str) -> datetime:
    jwt = {}
    for s in token.split(".")[0:2]:
        # Pad up the segment
        res = len(s) % 4
        if res != 0:
            s += "=" * (4 - res)

        d = base64.b64decode(s)
        jwt.update(json.loads(d))
    exp = datetime.fromtimestamp(jwt["exp"])
    return exp


def get_token_cache_path(envoy_serial: str) -> str:
    return os.path.join(user_cache_dir("enphase-envoy"), f"{envoy_serial}.token")


def get_cached_token(envoy_serial: str) -> Optional[str]:
    path = get_token_cache_path(envoy_serial)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        LOG.info("Using cached token from: %s", path)
        return f.read()


def save_token_to_cache(envoy_serial: str, token: str) -> None:
    path = get_token_cache_path(envoy_serial)
    LOG.info("Caching token to: %s", path)
    parent_dir = os.path.dirname(path)
    if not os.path.exists(parent_dir):
        os.mkdir(parent_dir)
    with open(path, "w", encoding="utf-8") as f:
        f.write(token)


def get_token(email: str, password: str, envoy_serial: str) -> str:
    """
    Do whatever it takes to get a token
    """
    token = get_cached_token(envoy_serial)
    if token is None:
        # cached token does not exist. Get a new one
        token = get_new_token(email, password, envoy_serial)
        save_token_to_cache(envoy_serial, token)

    exp = token_expiration_date(token)
    time_left = exp - datetime.now()
    if time_left < timedelta(days=1):
        # token will expire soon. get a new one
        LOG.info("Token will expire soon. Getting a new one")
        token = get_new_token(email, password, envoy_serial)
        save_token_to_cache(envoy_serial, token)

    return token
