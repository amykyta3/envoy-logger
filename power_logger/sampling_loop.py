from datetime import datetime, date, timezone
import time
from typing import List, Optional, Dict
import logging

from influxdb_client import WritePrecision, InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from . import envoy
from .model import SampleData, PowerSample, InverterSample, filter_new_inverter_data

class SamplingLoop:
    interval = 5

    def __init__(self, token: str, influxdb_url: str, influxdb_token: str, influxdb_org: str, influxdb_bucket_hr: str, influxdb_bucket_lr: str) -> None:
        self.session_id = envoy.login(token)
        self.influxdb_url = influxdb_url
        self.influxdb_token = influxdb_token
        self.influxdb_org = influxdb_org
        self.influxdb_bucket_hr = influxdb_bucket_hr
        self.influxdb_bucket_lr = influxdb_bucket_lr

        # Used to track the transition to the next day for daily measurements
        self.todays_date = date.today()
        self.todays_starting_values = {} # Dict[str, float]

        self.prev_inverter_data = None

    def run(self):
        while True:
            data = self.get_sample()
            inverter_data = self.get_inverter_data()
            self.write_to_influxdb(data, inverter_data)

    def get_sample(self) -> SampleData:
        # Determine how long until the next sample needs to be taken
        now = datetime.now()
        time_to_next = self.interval - (now.timestamp() % self.interval)

        # wait!
        time.sleep(time_to_next)

        data = envoy.get_power_data(self.session_id)

        return data

    def get_inverter_data(self) -> Dict[str, InverterSample]:
        data = envoy.get_inverter_data(self.session_id)

        if self.prev_inverter_data is None:
            self.prev_inverter_data = data
            # Hard to know how stale inverter data is, so discard this sample
            # since I have nothing to compare to yet
            return {}

        # filter out stale inverter samples
        filtered_data = filter_new_inverter_data(data, self.prev_inverter_data)
        if filtered_data:
            logging.info("Got %d unique inverter measurements", len(filtered_data))
        self.prev_inverter_data = data
        return filtered_data

    def write_to_influxdb(self, data: SampleData, inverter_data: Dict[str, InverterSample]) -> None:
        with InfluxDBClient(
            url=self.influxdb_url,
            token=self.influxdb_token,
            org=self.influxdb_org
        ) as client:
            hr_points = self.get_high_rate_points(data, inverter_data)
            lr_points = self.low_rate_points(data)
            with client.write_api(write_options=SYNCHRONOUS) as write_api:
                write_api.write(bucket=self.influxdb_bucket_hr, record=hr_points)
                if lr_points:
                    write_api.write(bucket=self.influxdb_bucket_lr, record=lr_points)

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
        p.tag("source", "power-meter")
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
        p.tag("source", "power-meter")
        p.tag("measurement-type", "inverter")
        p.tag("serial", inverter.serial)

        p.field("P", inverter.watts)

        return p

    def low_rate_points(self, data: SampleData) -> List[Point]:
        # First check if the day rolled over
        new_date = date.today()
        if self.todays_date == new_date:
            # still the same date. No summary
            return []

        # it is a new day!
        points = []
        if self.todays_starting_values:
            # Generate daily summary points
            # convert today's date to a datetime that is noon in the local timezone
            td = self.todays_date
            day_ts = datetime(td.year, td.month, td.day, 12).astimezone(timezone.utc)

            for i, line in enumerate(data.total_consumption.lines):
                p = self.get_daily_line_deltas("consumption", i, line, day_ts)
                points.append(p)
            for i, line in enumerate(data.total_production.lines):
                p = self.get_daily_line_deltas("production", i, line, day_ts)
                points.append(p)
            for i, line in enumerate(data.net_consumption.lines):
                p = self.get_daily_line_deltas("net", i, line, day_ts)
                points.append(p)

        # Also log cumulative totals
        for i, line in enumerate(data.total_consumption.lines):
            p = self.get_line_cumulative_totals("consumption", i, line)
            points.append(p)
        for i, line in enumerate(data.total_production.lines):
            p = self.get_line_cumulative_totals("production", i, line)
            points.append(p)
        for i, line in enumerate(data.net_consumption.lines):
            p = self.get_line_cumulative_totals("net", i, line)
            points.append(p)

        self.todays_date = new_date


        return points

    def get_daily_line_deltas(self, measurement_type: str, idx: int, data: PowerSample, day_ts: datetime) -> Point:
        p = Point(f"daily-{measurement_type}-line{idx}")
        p.time(day_ts, WritePrecision.S)
        p.tag("source", "power-meter")
        p.tag("measurement-type", measurement_type)
        p.tag("line-idx", idx)
        p.tag("interval", "24h")

        def add_field(name: str, data_prefix: str):
            # Compare increase from start of day
            key = (measurement_type, idx, name)
            abs_value = getattr(data, f"{data_prefix}Lifetime")
            value = abs_value - self.todays_starting_values[key]
            p.field(name, value)

            # Update for next day's measurement
            self.todays_starting_values[key] = abs_value

        add_field("Wh", "wh")
        add_field("VAh", "vah")
        add_field("VARh-Lag", "varhLag")
        add_field("VARh-Lead", "varhLead")

        return p

    def get_line_cumulative_totals(self, measurement_type: str, idx: int, data: PowerSample) -> Point:
        p = Point(f"{measurement_type}-cumulative-line{idx}")
        p.time(data.ts, WritePrecision.S)
        p.tag("source", "power-meter")
        p.tag("measurement-type", measurement_type)
        p.tag("line-idx", idx)
        p.tag("interval", "cumulative")

        p.field("Wh", data.whLifetime)
        p.field("VAh", data.vahLifetime)
        p.field("VARh-Lag", data.varhLagLifetime)
        p.field("VARh-Lead", data.varhLeadLifetime)

        return p
