from datetime import datetime
from typing import Dict
import logging

LOG = logging.getLogger("envoy")


class PowerSample:
    """
    A generic power sample
    """

    def __init__(self, data, ts: datetime) -> None:
        self.ts = ts

        # Instantaneous measurements
        self.wNow = data["wNow"]  # type: float
        self.rmsCurrent = data["rmsCurrent"]  # type: float
        self.rmsVoltage = data["rmsVoltage"]  # type: float
        self.reactPwr = data["reactPwr"]  # type: float
        self.apprntPwr = data["apprntPwr"]  # type: float

        # Historical measurements (Today)
        self.whToday = data["whToday"]  # type: float
        self.vahToday = data["vahToday"]  # type: float
        self.varhLagToday = data["varhLagToday"]  # type: float
        self.varhLeadToday = data["varhLeadToday"]  # type: float

        # Historical measurements (Lifetime)
        self.whLifetime = data["whLifetime"]  # type: float
        self.vahLifetime = data["vahLifetime"]  # type: float
        self.varhLagLifetime = data["varhLagLifetime"]  # type: float
        self.varhLeadLifetime = data["varhLeadLifetime"]  # type: float

        # Historical measurements (Other)
        self.whLastSevenDays = data["whLastSevenDays"]  # type: float

    @property
    def pwrFactor(self) -> float:
        # calculate power factor locally for better precision
        if self.apprntPwr < 10.0:
            return 1.0
        return self.wNow / self.apprntPwr


class EIMSample:
    """
    "EIM" measurement.

    Intentionally discard all total measurements.
    Envoy firmware has a bug where it miscalculates apparent power.
    Better to recalculate the values locally
    """

    def __init__(self, data, ts: datetime) -> None:
        assert data["type"] == "eim"

        # Do not use JSON data's timestamp. Envoy's clock is wrong
        self.ts = ts

        self.lines = []
        for line_data in data["lines"]:
            line = EIMLineSample(self, line_data)
            self.lines.append(line)

        LOG.debug(
            f"Sampled {len(self.lines)} power lines of type: {data['measurementType']}"
        )


class EIMLineSample(PowerSample):
    """
    Sample for a Single "EIM" line sensor
    """

    def __init__(self, parent: EIMSample, data) -> None:
        self.parent = parent
        super().__init__(data, parent.ts)


class SampleData:
    def __init__(self, data, ts: datetime) -> None:
        # Do not use JSON data's timestamp. Envoy's clock is wrong
        self.ts = ts

        self.net_consumption = None  # type: Optional[EIMSample]
        self.total_consumption = None  # type: Optional[EIMSample]
        self.total_production = None  # type: Optional[EIMSample]

        for consumption_data in data["consumption"]:
            if consumption_data["type"] == "eim":
                if consumption_data["measurementType"] == "net-consumption":
                    self.net_consumption = EIMSample(consumption_data, self.ts)
                if consumption_data["measurementType"] == "total-consumption":
                    self.total_consumption = EIMSample(consumption_data, self.ts)

        for production_data in data["production"]:
            if production_data["type"] == "eim":
                if production_data["measurementType"] == "production":
                    self.total_production = EIMSample(production_data, self.ts)
            if production_data["type"] == "inverters":
                # TODO: Parse this data too
                pass


# ===============================================================================
class InverterSample:
    def __init__(self, data, ts: datetime) -> None:
        # envoy time is not particularly accurate. Use my own ts
        self.ts = ts

        self.serial = data["serialNumber"]  # type: str
        self.report_ts = data["lastReportDate"]  # type: int
        self.watts = data["lastReportWatts"]  # type: int


def parse_inverter_data(data, ts: datetime) -> Dict[str, InverterSample]:
    """
    Parse inverter JSON list and return a dictionary of inverter samples, keyed
    by their serial number
    """
    inverters = {}

    for inverter_data in data:
        inverter = InverterSample(inverter_data, ts)
        inverters[inverter.serial] = inverter

    return inverters


def filter_new_inverter_data(
    new_data: Dict[str, InverterSample], prev_data: Dict[str, InverterSample]
) -> Dict[str, InverterSample]:
    """
    Inverter measurements only update if inverter actually sends a reported
    value.
    Compare against a prior sample, and return a new dict of inverters samples
    that only contains the unique measurements
    """
    unique_inverters = {}  # type: Dict[str, InverterSample]
    for serial, inverter in new_data.items():
        if serial not in prev_data.keys():
            unique_inverters[serial] = inverter
            continue

        if inverter.report_ts != prev_data[serial].report_ts:
            unique_inverters[serial] = inverter
            continue

    return unique_inverters
