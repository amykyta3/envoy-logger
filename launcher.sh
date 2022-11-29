#!/bin/sh
set -e

echo "Installing"
python3 -m pip install -U git+https://github.com/amykyta3/enphase-power-logger

echo "Starting logger"
python3 -m power_logger
