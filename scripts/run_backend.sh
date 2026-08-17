#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt

export AQUAFLOW_SIMULATE="${AQUAFLOW_SIMULATE:-1}"
export AQUAFLOW_PORT="${AQUAFLOW_PORT:-9090}"

echo "Starting AquaFlow backend (SIMULATE=$AQUAFLOW_SIMULATE)..."
python -m backend.app
