from datetime import datetime, date
import time
from typing import List, Dict
import logging
import sys
from requests.exceptions import ReadTimeout, ConnectTimeout

from influxdb_client import WritePrecision, InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from . import envoy
from .model import SampleData, PowerSample, InverterSample, filter_new_inverter_data
from .cfg import Config

class SamplingLoop:
    interval = 5

    def __init__(self, token: str, cfg: Config) -> None:
        self.cfg = cfg
        self.session_id = envoy.login(self.cfg.envoy_url, token)

        influxdb_client = InfluxDBClient(
            url=cfg.influxdb_url,
            token=cfg.influxdb_token,
            org=cfg.influxdb_org
        )
        self.influxdb_write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)
        self.influxdb_query_api = influxdb_client.query_api()

        # Used to track the transition to the next day for daily measurements
        self.todays_date = date.today()

        self.prev_inverter_data = None

    def run(self):
        timeout_count = 0
        while True:
            try:
                data = self.get_sample()
                inverter_data = self.get_inverter_data()
            except (ReadTimeout, ConnectTimeout) as e:
                # Envoy gets REALLY MAD if you block it's access to enphaseenergy.com
                # using a VLAN.
                # It's software gets hung up for some reason, and some requests will stall.
                # Allow envoy requests to timeout (and skip this sample iteration)
                timeout_count += 1
                logging.warning("Envoy request timed out (%d/10)", timeout_count)
                if timeout_count >= 10:
                    # Give up after a while
                    raise
                pass
            else:
                self.write_to_influxdb(data, inverter_data)
                timeout_count = 0

    def get_sample(self) -> SampleData:
        # Determine how long until the next sample needs to be taken
        now = datetime.now()
        time_to_next = self.interval - (now.timestamp() % self.interval)

        try:
            time.sleep(time_to_next)
        except KeyboardInterrupt:
            print('Exiting with Ctrl-C')
            sys.exit(0)

        data = envoy.get_power_data(self.cfg.envoy_url, self.session_id)

        return data

    def get_inverter_data(self) -> Dict[str, InverterSample]:
        data = envoy.get_inverter_data(self.cfg.envoy_url, self.session_id)

        if self.prev_inverter_data is None:
            self.prev_inverter_data = data
            # Hard to know how stale inverter data is, so discard this sample
            # since I have nothing to compare to yet
            return {}

        # filter out stale inverter samples
        filtered_data = filter_new_inverter_data(data, self.prev_inverter_data)
        if filtered_data:
            logging.debug("Got %d unique inverter measurements", len(filtered_data))
        self.prev_inverter_data = data
        return filtered_data

    def write_to_influxdb(self, data: SampleData, inverter_data: Dict[str, InverterSample]) -> None:
        hr_points = self.get_high_rate_points(data, inverter_data)
        lr_points = self.low_rate_points(data)
        self.influxdb_write_api.write(bucket=self.cfg.influxdb_bucket_hr, record=hr_points)
        if lr_points:
            self.influxdb_write_api.write(bucket=self.cfg.influxdb_bucket_lr, record=lr_points)

    def get_high_rate_points(self, data: SampleData, inverter_data: Dict[str, InverterSample]) -> List[Point]:
        points = []
        for i, line in enumerate(data.total_consumption.lines):
            p = self.idb_point_from_line("consumption", i, line)
            points.append(p)
        for i, line in enumerate(data.total_production.lines):
            p = self.idb_point_from_line("production", i, line)
            points.append(p)
        for i, line in enumerate(data.net_consumption.lines):
            p = self.idb_point_from_line("net", i, line)
            points.append(p)

        for inverter in inverter_data.values():
            p = self.point_from_inverter(inverter)
            points.append(p)

        return points

    def idb_point_from_line(self, measurement_type: str, idx: int, data: PowerSample) -> Point:
        p = Point(f"{measurement_type}-line{idx}")
        p.time(data.ts, WritePrecision.S)
        p.tag("source", self.cfg.source_tag)
        p.tag("measurement-type", measurement_type)
        p.tag("line-idx", idx)

        p.field("P", data.wNow)
        p.field("Q", data.reactPwr)
        p.field("S", data.apprntPwr)

        p.field("I_rms", data.rmsCurrent)
        p.field("V_rms", data.rmsVoltage)

        return p

    def point_from_inverter(self, inverter: InverterSample) -> Point:
        p = Point(f"inverter-production-{inverter.serial}")
        p.time(inverter.ts, WritePrecision.S)
        p.tag("source", self.cfg.source_tag)
        p.tag("measurement-type", "inverter")
        p.tag("serial", inverter.serial)
        self.cfg.apply_tags_to_inverter_point(p, inverter.serial)

        p.field("P", inverter.watts)

        return p

    def low_rate_points(self, data: SampleData) -> List[Point]:
        # First check if the day rolled over
        new_date = date.today()
        if self.todays_date == new_date:
            # still the same date. No summary
            return []

        # it is a new day!
        self.todays_date = new_date

        # Collect points that summarize prior day
        points = self.compute_daily_Wh_points(data.ts)

        return points

    def compute_daily_Wh_points(self, ts: datetime) -> List[Point]:
        # Not using integral(interpolate:"linear") since it does not do what you
        # think it would mean. Without the "interoplation" arg, it still does
        # linear interpolation correctly.
        # https://github.com/influxdata/flux/issues/4782
        query = f"""
        from(bucket: "{self.cfg.influxdb_bucket_hr}")
            |> range(start: -24h, stop: 0h)
            |> filter(fn: (r) => r["source"] == "{self.cfg.source_tag}")
            |> filter(fn: (r) => r["_field"] == "P")
            |> integral(unit: 1h)
            |> keep(columns: ["_value", "line-idx", "measurement-type", "serial"])
            |> yield(name: "total")
        """
        result = self.influxdb_query_api.query(query=query)
        unreported_inverters = set(self.cfg.inverters.keys())
        points = []
        for table in result:
            for record in table.records:
                measurement_type = record['measurement-type']
                if measurement_type == "inverter":
                    serial = record['serial']
                    unreported_inverters.discard(serial)
                    p = Point(f"inverter-daily-summary-{serial}")
                    p.tag("serial", serial)
                    self.cfg.apply_tags_to_inverter_point(p, serial)
                else:
                    idx = record['line-idx']
                    p = Point(f"{measurement_type}-daily-summary-line{idx}")
                    p.tag("line-idx", idx)

                p.time(ts, WritePrecision.S)
                p.tag("source", self.cfg.source_tag)
                p.tag("measurement-type", measurement_type)
                p.tag("interval", "24h")

                p.field("Wh", record.get_value())
                points.append(p)

        # If any inverters did not report in for the day, fill in a 0wh measurement
        for serial in unreported_inverters:
            p = Point(f"inverter-daily-summary-{serial}")
            p.tag("serial", serial)
            self.cfg.apply_tags_to_inverter_point(p, serial)
            p.time(ts, WritePrecision.S)
            p.tag("source", self.cfg.source_tag)
            p.tag("measurement-type", measurement_type)
            p.tag("interval", "24h")
            p.field("Wh", 0.0)
            points.append(p)

        return points
