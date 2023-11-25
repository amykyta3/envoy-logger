#!/usr/bin/env bash
set -eou pipefail
cd "$(dirname "${0}")"

poetry run black --check envoy_logger
poetry run flake8 envoy_logger

if which shellcheck; then
  shellcheck ./*.sh
fi
