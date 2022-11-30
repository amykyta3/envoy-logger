import logging
import os

from . import enphaseenergy
from .sampling_loop import SamplingLoop

logging.basicConfig(level=logging.INFO)

enphase_email = os.environ['ENPHASE_EMAIL']
enphase_password = os.environ['ENPHASE_PASSWORD']
envoy_serial = os.environ['ENVOY_SERIAL']
influxdb_url = os.environ['INFLUXDB_URL']
influxdb_token = os.environ['INFLUXDB_TOKEN']
influxdb_org = os.environ['INFLUXDB_ORG']
influxdb_bucket_hr = os.environ['INFLUXDB_BUCKET_HR']
influxdb_bucket_lr = os.environ['INFLUXDB_BUCKET_LR']

envoy_token = enphaseenergy.get_token(
    enphase_email,
    enphase_password,
    envoy_serial
)

S = SamplingLoop(
    envoy_token,
    influxdb_url,
    influxdb_token,
    influxdb_org,
    influxdb_bucket_hr,
    influxdb_bucket_lr,
)

S.run()
