FROM debian:bullseye-slim

COPY setup.py /opt/envoy_logger/
COPY envoy_logger /opt/envoy_logger/envoy_logger/
COPY docker/entrypoint.sh /opt/envoy_logger/entrypoint.sh

RUN \
  # Install dependencies
  apt update && \
  apt -y install python3 python3-pip git && \
  # Clean apt cache
  apt autoremove && \
  apt clean && \
  rm -rf /var/cache/apt && \
  # Install Python deps
  python3 -m pip install -U setuptools && \
  # Fix file permissions
  chmod a+x /opt/envoy_logger/entrypoint.sh

RUN python3 -m pip install /opt/envoy_logger

ENV ENVOY_LOGGER_CFG_PATH=/etc/envoy_logger/cfg.yaml
ENV ENVOY_LOGGER_DB=influxdb

ENTRYPOINT ["/opt/envoy_logger/entrypoint.sh"]
