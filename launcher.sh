#!/bin/sh
set -e

echo "Installing"
python3 -m pip install --force-reinstall git+https://github.com/amykyta3/envoy-logger

echo "Starting logger"
python3 -m envoy_logger $ENVOY_LOGGER_CFG_PATH
