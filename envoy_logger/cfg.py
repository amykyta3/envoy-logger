import logging
import sys

import yaml
from influxdb_client import Point

LOG = logging.getLogger("cfg")


class Config:
    def __init__(self, data) -> None:
        try:
            self.enphase_email = data["enphaseenergy"]["email"]  # type: str
            self.enphase_password = data["enphaseenergy"]["password"]  # type: str

            self.envoy_serial = str(data["envoy"]["serial"])
            self.envoy_url = data["envoy"].get(
                "url", "https://envoy.local"
            )  # type: str
            self.source_tag = data["envoy"].get("tag", "envoy")  # type: str

            self.influxdb_url = data["influxdb"]["url"]  # type: str
            self.influxdb_token = data["influxdb"]["token"]  # type: str
            self.influxdb_org = data["influxdb"].get("org", "home")  # type: str

            bucket = data["influxdb"].get("bucket", None)
            bucket_lr = data["influxdb"].get("bucket_lr", None)
            bucket_hr = data["influxdb"].get("bucket_hr", None)
            self.influxdb_bucket_lr = bucket_lr or bucket
            self.influxdb_bucket_hr = bucket_hr or bucket

            self.inverters = {}  # type: Dict[str, InverterConfig]
            for serial, inverter_data in data.get("inverters", {}).items():
                serial = str(serial)
                self.inverters[serial] = InverterConfig(inverter_data, serial)

        except KeyError as e:
            LOG.error("Missing required config key: %s", e.args[0])
            sys.exit(1)

    def apply_tags_to_inverter_point(self, p: Point, serial: str) -> None:
        if serial in self.inverters.keys():
            self.inverters[serial].apply_tags_to_point(p)


class InverterConfig:
    def __init__(self, data, serial) -> None:
        self.serial = serial
        self.tags = data.get("tags", {})

    def apply_tags_to_point(self, p: Point) -> None:
        for k, v in self.tags.items():
            p.tag(k, v)


def load_cfg(path: str):
    LOG.info("Loading config: %s", path)
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.load(f.read(), Loader=yaml.FullLoader)

    return Config(data)
