#!/usr/bin/env bash
set -euo pipefail

for service in catalog orders; do
  echo "==> Testing ${service}"
  python3 -m pip install -r "services/${service}/requirements.txt"
  PYTHONPATH="services/${service}" python3 -m unittest discover \
    -s "services/${service}" -p 'test_*.py'

  echo "==> Building ${service} image"
  docker build -t "${service}-service:local" "services/${service}"
done

echo "All unit tests and Docker builds passed."
